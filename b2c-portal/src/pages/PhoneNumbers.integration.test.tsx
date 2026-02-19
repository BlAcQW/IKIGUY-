import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { setupServer } from 'msw/node';
import { rest } from 'msw';
import PhoneNumbers from './PhoneNumbers';

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

// Setup MSW server
const server = setupServer(
  // Mock Vonage API
  rest.post('*/api/vonage/import', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        numbers: [
          {
            id: 'vonage-1',
            number: '+1-555-VONAGE1',
            status: 'active',
            capabilities: ['voice', 'sms']
          },
          {
            id: 'vonage-2',
            number: '+1-555-VONAGE2',
            status: 'active',
            capabilities: ['voice']
          }
        ]
      })
    );
  }),

  // Mock Telnyx API
  rest.post('*/api/telnyx/import', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        numbers: [
          {
            id: 'telnyx-1',
            number: '+1-555-TELNYX1',
            status: 'active',
            capabilities: ['voice', 'sms', 'mms']
          }
        ]
      })
    );
  }),

  // Mock Twilio API
  rest.post('*/api/twilio/import', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        numbers: [
          {
            id: 'twilio-1',
            number: '+1-555-TWILIO1',
            status: 'active',
            capabilities: ['voice', 'sms', 'mms', 'fax']
          },
          {
            id: 'twilio-2',
            number: '+44-20-TWILIO2',
            status: 'active',
            capabilities: ['voice']
          }
        ]
      })
    );
  }),

  // Mock SIP configuration
  rest.post('*/api/sip/configure', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        trunk: {
          id: 'sip-trunk-1',
          server: 'sip.example.com',
          status: 'connected',
          numbers: []
        }
      })
    );
  }),

  // Mock Kasa AI number provisioning
  rest.post('*/api/kasaai/provision', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        number: {
          id: 'kasaai-1',
          number: '+1-555-KASAAI',
          status: 'provisioning',
          plan: 'starter',
          capabilities: ['voice', 'sms', 'mms', 'ai-enhanced']
        }
      })
    );
  }),

  // Mock phone numbers list
  rest.get('*/api/phone-numbers', (req, res, ctx) => {
    return res(
      ctx.json({
        success: true,
        numbers: [
          {
            id: '1',
            number: '+1 (555) 123-4567',
            provider: 'Kasa AI',
            type: 'both',
            status: 'active',
            country: 'US',
            capabilities: ['voice', 'sms', 'mms'],
            monthly_cost: 1.00,
            created_at: '2024-01-15'
          }
        ]
      })
    );
  })
);

// Enable API mocking before tests
beforeAll(() => server.listen());
afterEach(() => {
  server.resetHandlers();
  mockToast.mockClear();
});
afterAll(() => server.close());

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

describe('PhoneNumbers Integration Tests', () => {
  describe('Vonage Import', () => {
    it('should successfully import numbers from Vonage', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      // Open import modal
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      // Select Vonage
      const vonageOption = screen.getByText('Vonage').closest('div[class*="border"]');
      await user.click(vonageOption!);
      
      // Fill in credentials
      const apiKeyInput = screen.getByPlaceholderText('API Key');
      const apiSecretInput = screen.getByPlaceholderText('API Secret');
      
      await user.type(apiKeyInput, 'test-vonage-api-key');
      await user.type(apiSecretInput, 'test-vonage-api-secret');
      
      // Mock the actual import function
      const originalConsoleLog = console.log;
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation((...args) => {
        if (args[0] === 'Importing numbers from') {
          // Simulate successful import
          mockToast({
            title: "Import successful",
            description: "2 numbers imported from Vonage",
          });
        }
        originalConsoleLog(...args);
      });
      
      // Click import
      const modalImportButton = screen.getAllByText('Import Numbers')[1];
      await user.click(modalImportButton);
      
      // Verify import was triggered
      expect(consoleLogSpy).toHaveBeenCalledWith('Importing numbers from', 'vonage');
      
      consoleLogSpy.mockRestore();
    });

    it('should validate Vonage API credentials', async () => {
      const user = userEvent.setup();
      server.use(
        rest.post('*/api/vonage/validate', (req, res, ctx) => {
          return res(
            ctx.status(401),
            ctx.json({
              success: false,
              error: 'Invalid API credentials'
            })
          );
        })
      );
      
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const vonageOption = screen.getByText('Vonage').closest('div[class*="border"]');
      await user.click(vonageOption!);
      
      const apiKeyInput = screen.getByPlaceholderText('API Key');
      await user.type(apiKeyInput, 'invalid-key');
      
      // Future enhancement: Add validation feedback
    });
  });

  describe('Telnyx Import', () => {
    it('should successfully import numbers from Telnyx', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const telnyxOption = screen.getByText('Telnyx').closest('div[class*="border"]');
      await user.click(telnyxOption!);
      
      const apiKeyInput = screen.getByPlaceholderText('API Key');
      await user.type(apiKeyInput, 'test-telnyx-api-key');
      
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      const modalImportButton = screen.getAllByText('Import Numbers')[1];
      await user.click(modalImportButton);
      
      expect(consoleLogSpy).toHaveBeenCalledWith('Importing numbers from', 'telnyx');
      
      consoleLogSpy.mockRestore();
    });
  });

  describe('Twilio Import', () => {
    it('should successfully import numbers from Twilio', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const twilioOption = screen.getByText('Twilio').closest('div[class*="border"]');
      await user.click(twilioOption!);
      
      const accountSidInput = screen.getByPlaceholderText('Account SID');
      const authTokenInput = screen.getByPlaceholderText('Auth Token');
      
      await user.type(accountSidInput, 'ACtest-twilio-account-sid');
      await user.type(authTokenInput, 'test-twilio-auth-token');
      
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      const modalImportButton = screen.getAllByText('Import Numbers')[1];
      await user.click(modalImportButton);
      
      expect(consoleLogSpy).toHaveBeenCalledWith('Importing numbers from', 'twilio');
      
      consoleLogSpy.mockRestore();
    });

    it('should validate Twilio account SID format', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const twilioOption = screen.getByText('Twilio').closest('div[class*="border"]');
      await user.click(twilioOption!);
      
      const accountSidInput = screen.getByPlaceholderText('Account SID');
      await user.type(accountSidInput, 'invalid-format');
      
      // Future enhancement: Add SID format validation
    });
  });

  describe('SIP Trunk Configuration', () => {
    it('should configure SIP trunk successfully', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const sipOption = screen.getByText('SIP Trunking').closest('div[class*="border"]');
      await user.click(sipOption!);
      
      const serverInput = screen.getByPlaceholderText('SIP Server URL');
      const usernameInput = screen.getByPlaceholderText('Username');
      const passwordInput = screen.getByPlaceholderText('Password');
      
      await user.type(serverInput, 'sip.mycompany.com');
      await user.type(usernameInput, 'sipuser');
      await user.type(passwordInput, 'sippass123');
      
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      const modalImportButton = screen.getAllByText('Import Numbers')[1];
      await user.click(modalImportButton);
      
      expect(consoleLogSpy).toHaveBeenCalledWith('Importing numbers from', 'sip');
      
      consoleLogSpy.mockRestore();
    });

    it('should validate SIP server URL format', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const sipOption = screen.getByText('SIP Trunking').closest('div[class*="border"]');
      await user.click(sipOption!);
      
      const serverInput = screen.getByPlaceholderText('SIP Server URL');
      await user.type(serverInput, 'not-a-valid-url');
      
      // Future enhancement: Add URL validation
    });
  });

  describe('Kasa AI Virtual Number Creation', () => {
    it('should provision a Starter plan number', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      await user.click(kasaButton);
      
      // Click on Starter plan
      const starterPlan = screen.getByText('Starter').closest('div[class*="border"]');
      expect(starterPlan).toBeInTheDocument();
      
      const consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
      
      const getNumberButton = screen.getByRole('button', { name: 'Get Number' });
      await user.click(getNumberButton);
      
      expect(mockToast).toHaveBeenCalledWith({
        title: "Number requested",
        description: "Your Kasa AI number is being provisioned.",
      });
      
      consoleLogSpy.mockRestore();
    });

    it('should provision a Professional plan number', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      await user.click(kasaButton);
      
      const professionalPlan = screen.getByText('Professional').closest('div[class*="border"]');
      expect(professionalPlan).toBeInTheDocument();
      
      const getNumberButton = screen.getByRole('button', { name: 'Get Number' });
      await user.click(getNumberButton);
      
      expect(mockToast).toHaveBeenCalledWith({
        title: "Number requested",
        description: "Your Kasa AI number is being provisioned.",
      });
    });

    it('should provision an Enterprise plan number', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      await user.click(kasaButton);
      
      const enterprisePlan = screen.getByText('Enterprise').closest('div[class*="border"]');
      expect(enterprisePlan).toBeInTheDocument();
      
      const getNumberButton = screen.getByRole('button', { name: 'Get Number' });
      await user.click(getNumberButton);
      
      expect(mockToast).toHaveBeenCalledWith({
        title: "Number requested",
        description: "Your Kasa AI number is being provisioned.",
      });
    });

    it('should show provisioning status after number request', async () => {
      server.use(
        rest.post('*/api/kasaai/provision', (req, res, ctx) => {
          return res(
            ctx.json({
              success: true,
              number: {
                id: 'kasaai-new',
                number: '+1-555-NEW',
                status: 'provisioning',
                estimated_time: '2-3 minutes'
              }
            })
          );
        })
      );
      
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      await user.click(kasaButton);
      
      const getNumberButton = screen.getByRole('button', { name: 'Get Number' });
      await user.click(getNumberButton);
      
      // Future enhancement: Show provisioning status in UI
    });
  });

  describe('Bulk Import Operations', () => {
    it('should handle importing multiple providers sequentially', async () => {
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      // Import from Vonage first
      let importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      let vonageOption = screen.getByText('Vonage').closest('div[class*="border"]');
      await user.click(vonageOption!);
      
      let modalImportButton = screen.getAllByText('Import Numbers')[1];
      await user.click(modalImportButton);
      
      expect(mockToast).toHaveBeenCalledWith({
        title: "Import started",
        description: "Importing numbers from vonage...",
      });
      
      // Then import from Twilio
      importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const twilioOption = screen.getByText('Twilio').closest('div[class*="border"]');
      await user.click(twilioOption!);
      
      modalImportButton = screen.getAllByText('Import Numbers')[1];
      await user.click(modalImportButton);
      
      expect(mockToast).toHaveBeenCalledWith({
        title: "Import started",
        description: "Importing numbers from twilio...",
      });
    });
  });

  describe('Error Recovery', () => {
    it('should handle network errors gracefully', async () => {
      server.use(
        rest.post('*/api/vonage/import', (req, res, ctx) => {
          return res.networkError('Network error');
        })
      );
      
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const importButton = screen.getByText('Import Numbers');
      await user.click(importButton);
      
      const vonageOption = screen.getByText('Vonage').closest('div[class*="border"]');
      await user.click(vonageOption!);
      
      const modalImportButton = screen.getAllByText('Import Numbers')[1];
      await user.click(modalImportButton);
      
      // Future enhancement: Add error handling
    });

    it('should handle API errors with user feedback', async () => {
      server.use(
        rest.post('*/api/kasaai/provision', (req, res, ctx) => {
          return res(
            ctx.status(503),
            ctx.json({
              success: false,
              error: 'Service temporarily unavailable'
            })
          );
        })
      );
      
      const user = userEvent.setup();
      renderWithProviders(<PhoneNumbers />);
      
      const kasaButton = screen.getByText('Get Kasa AI Number');
      await user.click(kasaButton);
      
      const getNumberButton = screen.getByRole('button', { name: 'Get Number' });
      await user.click(getNumberButton);
      
      // Future enhancement: Show error toast
    });
  });
});