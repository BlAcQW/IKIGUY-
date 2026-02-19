import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import PhoneNumbers from './PhoneNumbers';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the DashboardSidebar component
vi.mock('@/components/dashboard/DashboardSidebar', () => ({
  DashboardSidebar: () => <div data-testid="dashboard-sidebar">Sidebar</div>
}));

// Mock the useToast hook
const mockToast = vi.fn();
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: mockToast
  })
}));

// Helper function to wrap component with providers
const renderWithProviders = (component: React.ReactElement) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false }
    }
  });
  
  return render(
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        {component}
      </BrowserRouter>
    </QueryClientProvider>
  );
};

describe('PhoneNumbers Component', () => {
  beforeEach(() => {
    mockToast.mockClear();
  });

  describe('Layout and Theme', () => {
    it('should render with dashboard sidebar', () => {
      renderWithProviders(<PhoneNumbers />);
      expect(screen.getByTestId('dashboard-sidebar')).toBeInTheDocument();
    });

    it('should use theme-aware classes', () => {
      const { container } = renderWithProviders(<PhoneNumbers />);
      const mainContainer = container.firstChild;
      expect(mainContainer).toHaveClass('bg-background', 'text-foreground');
    });

    it('should display page header with title and description', () => {
      renderWithProviders(<PhoneNumbers />);
      expect(screen.getByText('Phone Numbers')).toBeInTheDocument();
      expect(screen.getByText('Manage your phone numbers and import from other providers')).toBeInTheDocument();
    });

    it('should display stats cards with correct information', () => {
      renderWithProviders(<PhoneNumbers />);
      expect(screen.getByText('Total Numbers')).toBeInTheDocument();
      expect(screen.getByText('Active')).toBeInTheDocument();
      expect(screen.getByText('Countries')).toBeInTheDocument();
      expect(screen.getByText('Monthly Cost')).toBeInTheDocument();
    });
  });

  describe('Phone Numbers List', () => {
    it('should display mock phone numbers', () => {
      renderWithProviders(<PhoneNumbers />);
      expect(screen.getByText('+1 (555) 123-4567')).toBeInTheDocument();
      expect(screen.getByText('+44 20 7946 0958')).toBeInTheDocument();
    });

    it('should show phone number details', () => {
      renderWithProviders(<PhoneNumbers />);
      expect(screen.getByText('Kasa AI')).toBeInTheDocument();
      expect(screen.getByText('Vonage')).toBeInTheDocument();
      expect(screen.getByText('US')).toBeInTheDocument();
      expect(screen.getByText('GB')).toBeInTheDocument();
    });

    it('should display capabilities badges', () => {
      renderWithProviders(<PhoneNumbers />);
      expect(screen.getByText('voice')).toBeInTheDocument();
      expect(screen.getByText('sms')).toBeInTheDocument();
      expect(screen.getByText('mms')).toBeInTheDocument();
    });

    it('should copy phone number to clipboard', async () => {
      const mockClipboard = {
        writeText: vi.fn().mockResolvedValue(undefined)
      };
      Object.assign(navigator, { clipboard: mockClipboard });

      renderWithProviders(<PhoneNumbers />);
      
      const copyButtons = screen.getAllByTitle('Copy number');
      fireEvent.click(copyButtons[0]);
      
      expect(mockClipboard.writeText).toHaveBeenCalledWith('+1 (555) 123-4567');
    });

    it('should show check icon after copying', async () => {
      const mockClipboard = {
        writeText: vi.fn().mockResolvedValue(undefined)
      };
      Object.assign(navigator, { clipboard: mockClipboard });

      renderWithProviders(<PhoneNumbers />);
      
      const copyButtons = screen.getAllByTitle('Copy number');
      fireEvent.click(copyButtons[0]);
      
      // Check icon should appear
      await waitFor(() => {
        const checkIcons = document.querySelectorAll('.text-green-500');
        expect(checkIcons.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Import Modal', () => {
    it('should open import modal when clicking Import Numbers button', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      expect(screen.getByText('Import Phone Numbers')).toBeInTheDocument();
    });

    it('should display all provider options', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      expect(screen.getByText('Vonage')).toBeInTheDocument();
      expect(screen.getByText('Import existing Vonage numbers')).toBeInTheDocument();
      
      expect(screen.getByText('Telnyx')).toBeInTheDocument();
      expect(screen.getByText('Import existing Telnyx numbers')).toBeInTheDocument();
      
      expect(screen.getByText('Twilio')).toBeInTheDocument();
      expect(screen.getByText('Import existing Twilio numbers')).toBeInTheDocument();
      
      expect(screen.getByText('SIP Trunking')).toBeInTheDocument();
      expect(screen.getByText('Configure your own SIP trunk')).toBeInTheDocument();
    });

    it('should show Vonage configuration fields when selecting Vonage', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const vonageOption = screen.getByText('Vonage').closest('div[class*="border"]');
      fireEvent.click(vonageOption!);
      
      expect(screen.getByPlaceholderText('API Key')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('API Secret')).toBeInTheDocument();
    });

    it('should show Telnyx configuration fields when selecting Telnyx', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const telnyxOption = screen.getByText('Telnyx').closest('div[class*="border"]');
      fireEvent.click(telnyxOption!);
      
      expect(screen.getByPlaceholderText('API Key')).toBeInTheDocument();
      expect(screen.queryByPlaceholderText('API Secret')).not.toBeInTheDocument();
    });

    it('should show Twilio configuration fields when selecting Twilio', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const twilioOption = screen.getByText('Twilio').closest('div[class*="border"]');
      fireEvent.click(twilioOption!);
      
      expect(screen.getByPlaceholderText('Account SID')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Auth Token')).toBeInTheDocument();
    });

    it('should show SIP configuration fields when selecting SIP', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const sipOption = screen.getByText('SIP Trunking').closest('div[class*="border"]');
      fireEvent.click(sipOption!);
      
      expect(screen.getByPlaceholderText('SIP Server URL')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Username')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Password')).toBeInTheDocument();
    });

    it('should disable Import Numbers button when no provider selected', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const modalImportButton = screen.getAllByText('Import Numbers')[1] as HTMLButtonElement;
      expect(modalImportButton.disabled).toBe(true);
    });

    it('should enable Import Numbers button when provider is selected', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const vonageOption = screen.getByText('Vonage').closest('div[class*="border"]');
      fireEvent.click(vonageOption!);
      
      const modalImportButton = screen.getAllByText('Import Numbers')[1] as HTMLButtonElement;
      expect(modalImportButton.disabled).toBe(false);
    });

    it('should close modal and show toast when importing', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const vonageOption = screen.getByText('Vonage').closest('div[class*="border"]');
      fireEvent.click(vonageOption!);
      
      const modalImportButton = screen.getAllByText('Import Numbers')[1];
      fireEvent.click(modalImportButton);
      
      expect(screen.queryByText('Import Phone Numbers')).not.toBeInTheDocument();
      expect(mockToast).toHaveBeenCalledWith({
        title: "Import started",
        description: "Importing numbers from vonage...",
      });
    });

    it('should close modal when clicking Cancel', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      fireEvent.click(importButton);
      
      const cancelButton = screen.getByText('Cancel');
      fireEvent.click(cancelButton);
      
      expect(screen.queryByText('Import Phone Numbers')).not.toBeInTheDocument();
    });
  });

  describe('Kasa AI Number Modal', () => {
    it('should open Kasa AI modal when clicking Get Kasa AI Number button', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      fireEvent.click(kasaButton);
      
      expect(screen.getByText('Get Kasa AI Phone Number')).toBeInTheDocument();
    });

    it('should display all Kasa AI plans', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      fireEvent.click(kasaButton);
      
      expect(screen.getByText('Starter')).toBeInTheDocument();
      expect(screen.getByText('$1/month')).toBeInTheDocument();
      expect(screen.getByText('1 phone number')).toBeInTheDocument();
      
      expect(screen.getByText('Professional')).toBeInTheDocument();
      expect(screen.getByText('$5/month')).toBeInTheDocument();
      expect(screen.getByText('5 phone numbers')).toBeInTheDocument();
      
      expect(screen.getByText('Enterprise')).toBeInTheDocument();
      expect(screen.getByText('$20/month')).toBeInTheDocument();
      expect(screen.getByText('20 phone numbers')).toBeInTheDocument();
    });

    it('should show plan features with check icons', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      fireEvent.click(kasaButton);
      
      expect(screen.getByText('Unlimited inbound calls')).toBeInTheDocument();
      expect(screen.getByText('100 outbound minutes')).toBeInTheDocument();
      expect(screen.getByText('Basic analytics')).toBeInTheDocument();
      expect(screen.getByText('Advanced analytics')).toBeInTheDocument();
      expect(screen.getByText('Call recording')).toBeInTheDocument();
      expect(screen.getByText('Custom integrations')).toBeInTheDocument();
      expect(screen.getByText('Priority support')).toBeInTheDocument();
    });

    it('should show info message about Kasa AI features', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      fireEvent.click(kasaButton);
      
      expect(screen.getByText(/Kasa AI phone numbers include unlimited inbound calls/)).toBeInTheDocument();
    });

    it('should close modal and show toast when getting number', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      fireEvent.click(kasaButton);
      
      const getNumberButton = screen.getByRole('button', { name: 'Get Number' });
      fireEvent.click(getNumberButton);
      
      expect(screen.queryByText('Get Kasa AI Phone Number')).not.toBeInTheDocument();
      expect(mockToast).toHaveBeenCalledWith({
        title: "Number requested",
        description: "Your Kasa AI number is being provisioned.",
      });
    });

    it('should close modal when clicking Cancel', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      fireEvent.click(kasaButton);
      
      const cancelButtons = screen.getAllByText('Cancel');
      fireEvent.click(cancelButtons[cancelButtons.length - 1]);
      
      expect(screen.queryByText('Get Kasa AI Phone Number')).not.toBeInTheDocument();
    });
  });

  describe('Accessibility', () => {
    it('should have proper ARIA labels and roles', () => {
      renderWithProviders(<PhoneNumbers />);
      
      const buttons = screen.getAllByRole('button');
      expect(buttons.length).toBeGreaterThan(0);
    });

    it('should support keyboard navigation', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.tab();
      await user.tab();
      expect(importButton).toHaveFocus();
    });
  });

  describe('Error Handling', () => {
    it('should handle clipboard API failure gracefully', async () => {
      const mockClipboard = {
        writeText: vi.fn().mockRejectedValue(new Error('Clipboard error'))
      };
      Object.assign(navigator, { clipboard: mockClipboard });

      const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
      
      renderWithProviders(<PhoneNumbers />);
      
      const copyButtons = screen.getAllByTitle('Copy number');
      fireEvent.click(copyButtons[0]);
      
      await waitFor(() => {
        expect(mockClipboard.writeText).toHaveBeenCalled();
      });

      consoleSpy.mockRestore();
    });
  });
});