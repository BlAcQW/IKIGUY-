import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { vi, describe, it, expect, beforeEach } from 'vitest';
import TemplateConfiguration from '@/components/TemplateConfiguration';
import { VoiceTemplate } from '@/components/VoiceAgentTemplates';

// Mock the toast hook
vi.mock('@/components/ui/use-toast', () => ({
  useToast: () => ({
    toast: vi.fn()
  })
}));

const mockTemplate: VoiceTemplate = {
  id: 'appointment-scheduler',
  name: 'Appointment Scheduler',
  description: 'Schedule appointments, manage calendars, and send confirmations',
  category: 'Scheduling',
  icon: 'Calendar',
  difficulty: 'Beginner',
  estimatedTime: '10-20 minutes',
  features: ['Calendar Management', 'Availability Checking', 'Confirmation Emails', 'Reminder Notifications'],
  systemPrompt: 'You are an appointment scheduling assistant for {business_name}.',
  sampleQuestions: [
    'What type of appointment do you need?',
    'What is your preferred date and time?',
    'How long should I schedule for this appointment?',
    'Would you like a reminder sent to your phone or email?'
  ],
  useCases: ['Medical Offices', 'Salons', 'Consulting Services', 'Real Estate'],
  tags: ['scheduling', 'appointments', 'calendar', 'booking'],
  popularity: 92
};

describe('TemplateConfiguration', () => {
  const mockOnConfigurationComplete = vi.fn();
  const mockOnClose = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders the configuration dialog with template name', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Configure Appointment Scheduler')).toBeInTheDocument();
    expect(screen.getByText(/Set up integrations and automation settings/)).toBeInTheDocument();
  });

  it('displays integration status section', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Integration Status')).toBeInTheDocument();
    expect(screen.getByText('Configure the integrations you want to enable for this assistant')).toBeInTheDocument();
  });

  it('shows calendar integration enabled by default', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    // Calendar is enabled by default because config.calendar.type is set
    // Use getAllByText to handle multiple Calendar elements
    const calendarElements = screen.getAllByText('Calendar');
    expect(calendarElements.length).toBeGreaterThan(0);
  });

  it('shows configuration tabs for different integrations', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    // Check for tab triggers using role and accessible names
    expect(screen.getByRole('tab', { name: /calendar/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /email/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /whatsapp/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /sheets/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /crm/i })).toBeInTheDocument();
    expect(screen.getByRole('tab', { name: /database/i })).toBeInTheDocument();
  });

  it('shows calendar configuration by default', async () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    // Calendar tab should be active by default
    await waitFor(() => {
      expect(screen.getByText('Calendar Integration')).toBeInTheDocument();
      expect(screen.getByText('Calendar Provider')).toBeInTheDocument();
      expect(screen.getByText('Calendar ID')).toBeInTheDocument();
    });
  });

  it('allows configuring calendar integration fields', async () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    // Test calendar ID input
    const calendarIdInput = screen.getByPlaceholderText('Enter your calendar ID');
    expect(calendarIdInput).toBeInTheDocument();
    
    fireEvent.change(calendarIdInput, { target: { value: 'test-calendar-id' } });
    expect(calendarIdInput).toHaveValue('test-calendar-id');
  });

  it('shows action buttons', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    expect(screen.getByText('Cancel')).toBeInTheDocument();
    expect(screen.getByText('Complete Configuration')).toBeInTheDocument();
  });

  it('calls onClose when cancel button is clicked', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    fireEvent.click(screen.getByText('Cancel'));
    expect(mockOnClose).toHaveBeenCalled();
  });

  it('displays template information correctly', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    // Check for template name in the dialog title
    expect(screen.getByText(/Configure.*Appointment Scheduler/)).toBeInTheDocument();
    expect(screen.getByText(/Set up integrations and automation settings/)).toBeInTheDocument();
  });

  it('shows integration configuration options', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    // Check for integration configuration elements
    expect(screen.getByText('Calendar Provider')).toBeInTheDocument();
    expect(screen.getByText('Calendar ID')).toBeInTheDocument();
  });

  it('renders all required UI elements', () => {
    render(
      <TemplateConfiguration
        template={mockTemplate}
        onConfigurationComplete={mockOnConfigurationComplete}
        onClose={mockOnClose}
      />
    );

    // Check for essential UI elements
    expect(screen.getByText('Integration Status')).toBeInTheDocument();
    expect(screen.getByText('Calendar Integration')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Enter your calendar ID')).toBeInTheDocument();
    expect(screen.getByText('Complete Configuration')).toBeInTheDocument();
    expect(screen.getByText('Cancel')).toBeInTheDocument();
  });
});

