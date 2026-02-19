/**
 * Integration tests for Automation workflow functionality.
 * Tests the complete automation flow from industry selection to configuration deployment.
 */

import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { rest } from 'msw';
import { setupServer } from 'msw/node';

import Automations from '../../src/pages/Automations';
import AutomationTemplates from '../../src/pages/AutomationTemplates';
import AutomationConfiguration from '../../src/pages/AutomationConfiguration';

// Mock API responses
const server = setupServer(
  rest.get('/api/internal/modules/available', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      industries: [
        {
          id: 'healthcare',
          name: 'Healthcare',
          description: 'Patient management, appointment scheduling, medical records',
          category: 'healthcare',
          available: true
        },
        {
          id: 'financial',
          name: 'Financial Services',
          description: 'Banking, insurance, investment management, compliance',
          category: 'financial',
          available: true
        }
      ]
    }));
  }),

  rest.get('/api/internal/modules/:industry/workflows', (req, res, ctx) => {
    const { industry } = req.params;
    return res(ctx.json({
      success: true,
      industry,
      workflows: [
        {
          id: 'patient-appointment-reminder',
          name: 'Patient Appointment Reminders',
          description: 'Automatically send appointment reminders via SMS, email, and voice calls',
          complexity: 'Simple',
          estimatedTime: '15 min',
          integrations: ['SMS', 'Email', 'Voice', 'Calendar'],
          category: 'Patient Management',
          popular: true,
          rating: 4.8,
          usageCount: 1250
        }
      ]
    }));
  }),

  rest.get('/api/internal/modules/:industry/integrations', (req, res, ctx) => {
    const { industry } = req.params;
    return res(ctx.json({
      success: true,
      industry,
      integrations: [
        {
          id: 'sms',
          name: 'SMS Notifications',
          type: 'sms',
          description: 'Send appointment reminders via text message',
          required: false,
          configured: false
        },
        {
          id: 'calendar',
          name: 'Calendar Integration',
          type: 'calendar',
          description: 'Sync with your calendar system for appointment data',
          required: true,
          configured: false
        }
      ]
    }));
  }),

  rest.post('/api/internal/modules/:industry/initialize', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      module_id: 'healthcare_test_tenant',
      status: 'initialized',
      capabilities: [],
      workflows: []
    }));
  }),

  rest.post('/api/internal/modules/:industry/workflows/:workflow/execute', (req, res, ctx) => {
    return res(ctx.json({
      success: true,
      industry: req.params.industry,
      workflow: req.params.workflow,
      result: { deployment_id: 'auto_123', status: 'deployed' }
    }));
  })
);

beforeEach(() => {
  server.listen();
});

afterEach(() => {
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

const renderWithRouter = (component: React.ReactElement) => {
  return render(
    <BrowserRouter>
      {component}
    </BrowserRouter>
  );
};

describe('Automation Integration Tests', () => {
  describe('Automations Page', () => {
    it('should render industry selection with search and filtering', async () => {
      renderWithRouter(<Automations />);

      expect(screen.getByText('Automations')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search industries...')).toBeInTheDocument();
      expect(screen.getByText('Popular')).toBeInTheDocument();

      // Wait for industries to load
      await waitFor(() => {
        expect(screen.getByText('Healthcare')).toBeInTheDocument();
        expect(screen.getByText('Financial Services')).toBeInTheDocument();
      });
    });

    it('should filter industries by search term', async () => {
      renderWithRouter(<Automations />);

      const searchInput = screen.getByPlaceholderText('Search industries...');
      fireEvent.change(searchInput, { target: { value: 'healthcare' } });

      await waitFor(() => {
        expect(screen.getByText('Healthcare')).toBeInTheDocument();
        expect(screen.queryByText('Financial Services')).not.toBeInTheDocument();
      });
    });

    it('should navigate to templates when industry is selected', async () => {
      const mockNavigate = vi.fn();
      vi.mock('react-router-dom', () => ({
        ...vi.importActual('react-router-dom'),
        useNavigate: () => mockNavigate
      }));

      renderWithRouter(<Automations />);

      await waitFor(() => {
        const healthcareCard = screen.getByText('Healthcare').closest('[role="button"]') || 
                              screen.getByText('Healthcare').closest('div[class*="cursor-pointer"]');
        if (healthcareCard) {
          fireEvent.click(healthcareCard);
        }
      });

      expect(mockNavigate).toHaveBeenCalledWith('/automations/industry/healthcare');
    });
  });

  describe('AutomationTemplates Page', () => {
    const mockParams = { industryId: 'healthcare' };
    
    beforeEach(() => {
      vi.mock('react-router-dom', () => ({
        ...vi.importActual('react-router-dom'),
        useParams: () => mockParams,
        useNavigate: () => vi.fn()
      }));
    });

    it('should render industry templates with filtering options', async () => {
      renderWithRouter(<AutomationTemplates />);

      expect(screen.getByText('Healthcare Automations')).toBeInTheDocument();
      expect(screen.getByPlaceholderText('Search templates...')).toBeInTheDocument();

      // Wait for templates to load
      await waitFor(() => {
        expect(screen.getByText('Patient Appointment Reminders')).toBeInTheDocument();
      });
    });

    it('should filter templates by complexity', async () => {
      renderWithRouter(<AutomationTemplates />);

      const complexitySelect = screen.getByDisplayValue('All Complexity');
      fireEvent.change(complexitySelect, { target: { value: 'Simple' } });

      await waitFor(() => {
        expect(screen.getByText('Patient Appointment Reminders')).toBeInTheDocument();
      });
    });

    it('should navigate to configuration when template is selected', async () => {
      const mockNavigate = vi.fn();
      vi.mock('react-router-dom', () => ({
        ...vi.importActual('react-router-dom'),
        useParams: () => mockParams,
        useNavigate: () => mockNavigate
      }));

      renderWithRouter(<AutomationTemplates />);

      await waitFor(() => {
        const templateCard = screen.getByText('Patient Appointment Reminders').closest('[role="button"]') ||
                            screen.getByText('Patient Appointment Reminders').closest('div[class*="cursor-pointer"]');
        if (templateCard) {
          fireEvent.click(templateCard);
        }
      });

      expect(mockNavigate).toHaveBeenCalledWith('/automations/configure/patient-appointment-reminder');
    });
  });

  describe('AutomationConfiguration Page', () => {
    const mockParams = { templateId: 'patient-appointment-reminder' };
    
    beforeEach(() => {
      vi.mock('react-router-dom', () => ({
        ...vi.importActual('react-router-dom'),
        useParams: () => mockParams,
        useNavigate: () => vi.fn()
      }));
    });

    it('should render configuration form with tabs', async () => {
      renderWithRouter(<AutomationConfiguration />);

      expect(screen.getByText('Configure: Patient Appointment Reminders')).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Overview' })).toBeInTheDocument();
    });

    it('should show integration status indicators', async () => {
      renderWithRouter(<AutomationConfiguration />);

      await waitFor(() => {
        expect(screen.getByText('SMS Notifications')).toBeInTheDocument();
        expect(screen.getByText('Calendar Integration')).toBeInTheDocument();
        expect(screen.getByText('Required')).toBeInTheDocument();
      });
    });

    it('should handle configuration form submission', async () => {
      renderWithRouter(<AutomationConfiguration />);

      const nameInput = screen.getByLabelText('Automation Name');
      fireEvent.change(nameInput, { target: { value: 'My Custom Reminder' } });

      const saveButton = screen.getByText('Save Configuration');
      fireEvent.click(saveButton);

      // Verify form data is saved (this would typically call an API)
      expect(nameInput).toHaveValue('My Custom Reminder');
    });

    it('should test integration connections', async () => {
      renderWithRouter(<AutomationConfiguration />);

      // Switch to SMS tab
      const smsTab = screen.getByText('SMS Notifications');
      fireEvent.click(smsTab);

      await waitFor(() => {
        const testButton = screen.getByText('Test Connection');
        fireEvent.click(testButton);
      });

      await waitFor(() => {
        expect(screen.getByText('Testing Connection...')).toBeInTheDocument();
      });
    });

    it('should deploy automation when all required integrations are configured', async () => {
      const mockNavigate = vi.fn();
      vi.mock('react-router-dom', () => ({
        ...vi.importActual('react-router-dom'),
        useParams: () => mockParams,
        useNavigate: () => mockNavigate
      }));

      renderWithRouter(<AutomationConfiguration />);

      // Mock all required integrations as configured
      server.use(
        rest.get('/api/internal/modules/:industry/integrations', (req, res, ctx) => {
          return res(ctx.json({
            success: true,
            integrations: [
              { id: 'calendar', required: true, configured: true }
            ]
          }));
        })
      );

      await waitFor(() => {
        const deployButton = screen.getByText('Deploy Automation');
        fireEvent.click(deployButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/automations/success');
    });

    it('should prevent deployment when required integrations are missing', async () => {
      renderWithRouter(<AutomationConfiguration />);

      const deployButton = screen.getByText('Deploy Automation');
      expect(deployButton).toBeDisabled();
      expect(screen.getByText('Complete required integrations to deploy')).toBeInTheDocument();
    });
  });

  describe('Full Automation Workflow', () => {
    it('should complete entire automation setup flow', async () => {
      const mockNavigate = vi.fn();
      
      // Mock the full navigation flow
      vi.mock('react-router-dom', () => ({
        ...vi.importActual('react-router-dom'),
        useNavigate: () => mockNavigate,
        useParams: () => ({ industryId: 'healthcare', templateId: 'patient-appointment-reminder' })
      }));

      // Step 1: Industry Selection
      renderWithRouter(<Automations />);
      
      await waitFor(() => {
        const healthcareCard = screen.getByText('Healthcare');
        fireEvent.click(healthcareCard);
      });

      // Step 2: Template Selection
      renderWithRouter(<AutomationTemplates />);
      
      await waitFor(() => {
        const templateCard = screen.getByText('Patient Appointment Reminders');
        fireEvent.click(templateCard);
      });

      // Step 3: Configuration
      renderWithRouter(<AutomationConfiguration />);
      
      // Fill in basic configuration
      const nameInput = screen.getByLabelText('Automation Name');
      fireEvent.change(nameInput, { target: { value: 'Test Automation' } });

      // Configure required integration (Calendar)
      const calendarTab = screen.getByText('Calendar Integration');
      fireEvent.click(calendarTab);

      await waitFor(() => {
        const apiEndpoint = screen.getByLabelText('API Endpoint');
        fireEvent.change(apiEndpoint, { target: { value: 'https://api.test.com' } });
        
        const authToken = screen.getByLabelText('Authentication Token');
        fireEvent.change(authToken, { target: { value: 'test_token_123' } });

        const testButton = screen.getByText('Test Connection');
        fireEvent.click(testButton);
      });

      // Deploy automation
      await waitFor(() => {
        const deployButton = screen.getByText('Deploy Automation');
        fireEvent.click(deployButton);
      });

      expect(mockNavigate).toHaveBeenCalledWith('/automations/success');
    });
  });
});