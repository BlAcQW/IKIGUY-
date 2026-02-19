import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import { HelpdeskCampaignWizard } from '../HelpdeskCampaignWizard';
import type { CampaignTemplate } from '../CampaignTemplateSelector';

// Mock the toast hook
vi.mock('@/hooks/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

const mockTemplate: CampaignTemplate = {
  id: 'helpdesk_support',
  name: 'Helpdesk Support Agent',
  description: 'AI-powered helpdesk with appointment booking, ticket management, and availability lookup',
  category: 'support',
  icon: () => <div>HeadphonesIcon</div>,
  difficulty: 'advanced',
  estimatedSetupTime: '30-40 minutes',
  features: [
    'Appointment booking',
    'Availability lookup',
    'Ticket system integration',
    'N8N workflow automation',
    'VAPI voice agent',
    'Calendar integration',
    'Real-time availability',
    'Escalation management'
  ],
  defaultIntegrations: ['n8n', 'vapi', 'google_workspace', 'calendar', 'ticket_system', 'email', 'sms'],
  sampleData: {
    expectedResponses: 75,
    conversionRate: '60-80%',
    avgCallDuration: '4-7 minutes'
  },
  previewScript: 'Hello! I\'m your AI helpdesk assistant...',
  n8nConfig: {
    enabled: true,
    workflowType: 'helpdesk_automation',
    endpoints: ['calendar_lookup', 'ticket_creation', 'availability_check', 'escalation_routing']
  },
  vapiConfig: {
    enabled: true,
    assistantType: 'helpdesk_agent',
    features: ['appointment_booking', 'ticket_management', 'availability_lookup', 'escalation_handling']
  }
};

const defaultProps = {
  isOpen: true,
  onClose: vi.fn(),
  template: mockTemplate,
  onCreateCampaign: vi.fn(),
  apiBaseUrl: 'https://api.test.com'
};

describe('HelpdeskCampaignWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the wizard with correct title and first step', () => {
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    expect(screen.getByText('Setup Helpdesk Campaign')).toBeInTheDocument();
    expect(screen.getByText('Step 1 of 7: Basic Setup')).toBeInTheDocument();
    expect(screen.getByText('Campaign Name')).toBeInTheDocument();
  });

  it('allows user to fill in basic campaign information', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    const nameInput = screen.getByLabelText('Campaign Name');
    const descriptionInput = screen.getByLabelText('Description');
    const phoneInput = screen.getByLabelText('Phone Number');

    await user.type(nameInput, 'Test Helpdesk Campaign');
    await user.type(descriptionInput, 'Test description for helpdesk');
    await user.type(phoneInput, '+1234567890');

    expect(nameInput).toHaveValue('Test Helpdesk Campaign');
    expect(descriptionInput).toHaveValue('Test description for helpdesk');
    expect(phoneInput).toHaveValue('+1234567890');
  });

  it('navigates through wizard steps correctly', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    // Fill in required fields for step 1
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');

    // Navigate to next step
    const nextButton = screen.getByText('Next');
    await user.click(nextButton);

    expect(screen.getByText('Step 2 of 7: Voice Agent')).toBeInTheDocument();
    expect(screen.getByText('Voice Agent Configuration')).toBeInTheDocument();
  });

  it('shows VAPI configuration fields in step 2', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    // Navigate to VAPI step
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');
    await user.click(screen.getByText('Next'));

    expect(screen.getByText('Voice Agent Configuration')).toBeInTheDocument();
    expect(screen.getByLabelText('Assistant ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Phone Number ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Voice')).toBeInTheDocument();
    expect(screen.getByLabelText('AI Model')).toBeInTheDocument();
  });

  it('shows N8N workflow configuration in step 3', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    // Navigate to N8N step
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');
    await user.click(screen.getByText('Next')); // Step 2
    await user.click(screen.getByText('Next')); // Step 3

    expect(screen.getByText('Step 3 of 7: Workflow')).toBeInTheDocument();
    expect(screen.getByText('N8N Workflow Integration')).toBeInTheDocument();
    expect(screen.getByLabelText('Workflow ID')).toBeInTheDocument();
    expect(screen.getByLabelText('Webhook URL')).toBeInTheDocument();
  });

  it('shows calendar integration configuration in step 4', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    // Navigate to calendar step
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');
    for (let i = 0; i < 3; i++) {
      await user.click(screen.getByText('Next'));
    }

    expect(screen.getByText('Step 4 of 7: Calendar')).toBeInTheDocument();
    expect(screen.getByText('Calendar Integration')).toBeInTheDocument();
    expect(screen.getByLabelText('Provider')).toBeInTheDocument();
    expect(screen.getByLabelText('Calendar ID')).toBeInTheDocument();
  });

  it('allows toggling of business hours', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    // Navigate to business hours step
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');
    for (let i = 0; i < 5; i++) {
      await user.click(screen.getByText('Next'));
    }

    expect(screen.getByText('Step 6 of 7: Business Hours')).toBeInTheDocument();
    expect(screen.getByText('Business Hours')).toBeInTheDocument();

    // Business hours should be enabled by default
    const businessHoursToggle = screen.getByRole('switch');
    expect(businessHoursToggle).toBeChecked();

    // Toggle off
    await user.click(businessHoursToggle);
    expect(businessHoursToggle).not.toBeChecked();
  });

  it('shows configuration review in final step', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    // Navigate to final step
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');
    for (let i = 0; i < 6; i++) {
      await user.click(screen.getByText('Next'));
    }

    expect(screen.getByText('Step 7 of 7: Review')).toBeInTheDocument();
    expect(screen.getByText('Configuration Review')).toBeInTheDocument();
    expect(screen.getByText('Basic Information')).toBeInTheDocument();
    expect(screen.getByText('Voice Agent')).toBeInTheDocument();
    expect(screen.getByText('Integrations')).toBeInTheDocument();
  });

  it('calls onCreateCampaign when Create Campaign is clicked', async () => {
    const user = userEvent.setup();
    const mockOnCreate = vi.fn().mockResolvedValue({});
    render(<HelpdeskCampaignWizard {...defaultProps} onCreateCampaign={mockOnCreate} />);

    // Navigate to final step
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');
    for (let i = 0; i < 6; i++) {
      await user.click(screen.getByText('Next'));
    }

    // Click Create Campaign
    const createButton = screen.getByText('Create Campaign');
    await user.click(createButton);

    await waitFor(() => {
      expect(mockOnCreate).toHaveBeenCalledWith(expect.objectContaining({
        name: 'Test Campaign'
      }));
    });
  });

  it('allows going back to previous steps', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    // Navigate to step 2
    await user.type(screen.getByLabelText('Campaign Name'), 'Test Campaign');
    await user.click(screen.getByText('Next'));

    expect(screen.getByText('Step 2 of 7: Voice Agent')).toBeInTheDocument();

    // Go back to step 1
    await user.click(screen.getByText('Previous'));

    expect(screen.getByText('Step 1 of 7: Basic Setup')).toBeInTheDocument();
  });

  it('disables Previous button on first step', () => {
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    const previousButton = screen.getByText('Previous');
    expect(previousButton).toBeDisabled();
  });

  it('calls onClose when Cancel is clicked', async () => {
    const user = userEvent.setup();
    const mockOnClose = vi.fn();
    render(<HelpdeskCampaignWizard {...defaultProps} onClose={mockOnClose} />);

    const cancelButton = screen.getByText('Cancel');
    await user.click(cancelButton);

    expect(mockOnClose).toHaveBeenCalled();
  });

  it('updates configuration when form fields change', async () => {
    const user = userEvent.setup();
    render(<HelpdeskCampaignWizard {...defaultProps} />);

    const nameInput = screen.getByLabelText('Campaign Name');
    await user.type(nameInput, 'Updated Campaign Name');

    // Navigate to next step and back to verify persistence
    await user.click(screen.getByText('Next'));
    await user.click(screen.getByText('Previous'));

    expect(nameInput).toHaveValue('Updated Campaign Name');
  });
});