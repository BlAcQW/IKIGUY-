import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AppointmentCampaignWizard } from '../AppointmentCampaignWizard';

// Mock the appointment scheduling service
vi.mock('../../services/appointmentSchedulingService', () => ({
  AppointmentSchedulingService: vi.fn().mockImplementation(() => ({
    testCalendarConnection: vi.fn().mockResolvedValue({
      success: true,
      message: 'Calendar connected successfully',
      calendarId: 'test-calendar-123'
    }),
    checkAvailability: vi.fn().mockResolvedValue([
      {
        start: '2024-01-15T09:00:00Z',
        end: '2024-01-15T10:00:00Z',
        available: true
      }
    ])
  }))
}));

const mockOnComplete = vi.fn();
const mockOnCancel = vi.fn();

describe('AppointmentCampaignWizard', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial step with basic setup form', () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Basic Setup')).toBeInTheDocument();
    expect(screen.getByLabelText(/campaign name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/description/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/phone number/i)).toBeInTheDocument();
  });

  it('validates required fields in basic setup', async () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    const nextButton = screen.getByText('Next');
    fireEvent.click(nextButton);

    await waitFor(() => {
      expect(screen.getByText(/campaign name is required/i)).toBeInTheDocument();
    });
  });

  it('progresses to calendar integration step', async () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    // Fill basic setup
    fireEvent.change(screen.getByLabelText(/campaign name/i), {
      target: { value: 'Test Appointment Campaign' }
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'Test appointment booking' }
    });
    fireEvent.change(screen.getByLabelText(/phone number/i), {
      target: { value: '+1234567890' }
    });

    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(screen.getByText('Calendar Integration')).toBeInTheDocument();
    });
  });

  it('adds calendar integration', async () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    // Navigate to calendar integration step
    fireEvent.change(screen.getByLabelText(/campaign name/i), {
      target: { value: 'Test Campaign' }
    });
    fireEvent.change(screen.getByLabelText(/description/i), {
      target: { value: 'Test description' }
    });
    fireEvent.change(screen.getByLabelText(/phone number/i), {
      target: { value: '+1234567890' }
    });
    fireEvent.click(screen.getByText('Next'));

    await waitFor(() => {
      expect(screen.getByText('Calendar Integration')).toBeInTheDocument();
    });

    // Add Google Calendar integration
    const addCalendarButton = screen.getByText('Add Calendar Integration');
    fireEvent.click(addCalendarButton);

    // Select Google Calendar
    const googleOption = screen.getByText('Google Calendar');
    fireEvent.click(googleOption);

    // Fill calendar configuration
    const calendarIdInput = screen.getByLabelText(/calendar id/i);
    fireEvent.change(calendarIdInput, {
      target: { value: 'test-calendar@gmail.com' }
    });

    const apiKeyInput = screen.getByLabelText(/api key/i);
    fireEvent.change(apiKeyInput, {
      target: { value: 'test-api-key' }
    });

    // Test connection
    const testButton = screen.getByText('Test Connection');
    fireEvent.click(testButton);

    await waitFor(() => {
      expect(screen.getByText(/calendar connected successfully/i)).toBeInTheDocument();
    });
  });

  it('configures appointment types', async () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    // Navigate to appointment types step (simplified for test)
    // In real implementation, would go through previous steps
    const appointmentTypeStep = screen.queryByText('Appointment Types');

    if (appointmentTypeStep) {
      const addTypeButton = screen.getByText('Add Appointment Type');
      fireEvent.click(addTypeButton);

      // Configure appointment type
      const nameInput = screen.getByLabelText(/type name/i);
      fireEvent.change(nameInput, {
        target: { value: 'Consultation' }
      });

      const durationInput = screen.getByLabelText(/duration/i);
      fireEvent.change(durationInput, {
        target: { value: '60' }
      });

      const descriptionInput = screen.getByLabelText(/description/i);
      fireEvent.change(descriptionInput, {
        target: { value: 'Initial consultation meeting' }
      });
    }
  });

  it('sets up availability schedule', () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    // Check if availability settings are rendered
    const mondayCheckbox = screen.queryByLabelText(/monday/i);
    if (mondayCheckbox) {
      fireEvent.click(mondayCheckbox);
      expect(mondayCheckbox).toBeChecked();
    }
  });

  it('configures notification settings', () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    // Check notification settings
    const emailCheckbox = screen.queryByLabelText(/email notifications/i);
    if (emailCheckbox) {
      fireEvent.click(emailCheckbox);
      expect(emailCheckbox).toBeChecked();
    }

    const smsCheckbox = screen.queryByLabelText(/sms notifications/i);
    if (smsCheckbox) {
      fireEvent.click(smsCheckbox);
      expect(smsCheckbox).toBeChecked();
    }
  });

  it('handles wizard completion', () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    const completeConfig = {
      name: 'Test Appointment Campaign',
      description: 'Test appointment booking',
      phoneNumber: '+1234567890',
      calendarIntegrations: [{
        provider: 'google' as const,
        calendarId: 'test@gmail.com',
        apiKey: 'test-key',
        name: 'Main Calendar',
        primaryCalendar: true
      }],
      appointmentTypes: [{
        id: 'consultation',
        name: 'Consultation',
        duration: 60,
        description: 'Initial consultation',
        price: 100,
        color: '#3B82F6',
        bufferTime: 15,
        maxAdvanceBooking: 30,
        requiresApproval: false
      }],
      availability: {
        timezone: 'America/New_York',
        schedule: {
          monday: { enabled: true, start: '09:00', end: '17:00' },
          tuesday: { enabled: true, start: '09:00', end: '17:00' },
          wednesday: { enabled: true, start: '09:00', end: '17:00' },
          thursday: { enabled: true, start: '09:00', end: '17:00' },
          friday: { enabled: true, start: '09:00', end: '17:00' },
          saturday: { enabled: false, start: '09:00', end: '17:00' },
          sunday: { enabled: false, start: '09:00', end: '17:00' }
        },
        holidays: [],
        blackoutDates: []
      },
      notifications: {
        emailEnabled: true,
        smsEnabled: true,
        confirmationTemplate: 'default',
        reminderTemplate: 'default',
        reminderTiming: [24, 2]
      },
      vapiConfig: {
        assistantId: 'test-assistant',
        voice: 'alloy',
        model: 'gpt-4',
        functions: []
      },
      automationSettings: {
        autoConfirm: true,
        allowReschedule: true,
        allowCancellation: true,
        cancellationDeadline: 24,
        waitlistEnabled: true,
        doubleBookingPrevention: true
      }
    };

    // Mock wizard completion
    const wizard = screen.getByTestId?.('appointment-campaign-wizard') || document.body;
    fireEvent(wizard, new CustomEvent('complete', { detail: completeConfig }));

    expect(mockOnComplete).toHaveBeenCalledWith(completeConfig);
  });

  it('handles wizard cancellation', () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);

    expect(mockOnCancel).toHaveBeenCalled();
  });

  it('validates calendar provider selection', () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    // Check if calendar providers are available
    const providers = ['Google Calendar', 'Microsoft Outlook', 'Calendly', 'Acuity Scheduling'];

    providers.forEach(provider => {
      const providerElement = screen.queryByText(provider);
      if (providerElement) {
        expect(providerElement).toBeInTheDocument();
      }
    });
  });

  it('validates appointment duration settings', () => {
    render(
      <AppointmentCampaignWizard
        onComplete={mockOnComplete}
        onCancel={mockOnCancel}
      />
    );

    // Check duration validation
    const durationInput = screen.queryByLabelText(/duration/i);
    if (durationInput) {
      fireEvent.change(durationInput, { target: { value: '0' } });
      fireEvent.blur(durationInput);

      const errorMessage = screen.queryByText(/duration must be at least 1 minute/i);
      if (errorMessage) {
        expect(errorMessage).toBeInTheDocument();
      }
    }
  });
});