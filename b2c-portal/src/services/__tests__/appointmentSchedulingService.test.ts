import { describe, it, expect, vi, beforeEach } from 'vitest';
import { AppointmentSchedulingService } from '../appointmentSchedulingService';

// Mock fetch globally
global.fetch = vi.fn();

describe('AppointmentSchedulingService', () => {
  let service: AppointmentSchedulingService;

  beforeEach(() => {
    vi.clearAllMocks();
    service = new AppointmentSchedulingService([
      {
        provider: 'google',
        calendarId: 'test@gmail.com',
        apiKey: 'test-api-key',
        name: 'Test Calendar',
        primaryCalendar: true
      }
    ]);
  });

  describe('Calendar Connection', () => {
    it('successfully tests Google Calendar connection', async () => {
      const mockCalendarResponse = {
        id: 'test@gmail.com',
        summary: 'Test Calendar',
        timeZone: 'America/New_York'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockCalendarResponse
      });

      const result = await service.testCalendarConnection('google', {
        calendarId: 'test@gmail.com',
        apiKey: 'test-api-key'
      });

      expect(result.success).toBe(true);
      expect(result.calendarId).toBe('test@gmail.com');
    });

    it('handles calendar connection failure', async () => {
      (fetch as any).mockRejectedValueOnce(new Error('Invalid credentials'));

      const result = await service.testCalendarConnection('google', {
        calendarId: 'test@gmail.com',
        apiKey: 'invalid-key'
      });

      expect(result.success).toBe(false);
      expect(result.message).toContain('Failed to connect');
    });

    it('tests Outlook calendar connection', async () => {
      const mockOutlookResponse = {
        id: 'outlook-calendar-123',
        name: 'Outlook Calendar'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOutlookResponse
      });

      const result = await service.testCalendarConnection('outlook', {
        calendarId: 'outlook-calendar-123',
        accessToken: 'outlook-token'
      });

      expect(result.success).toBe(true);
    });
  });

  describe('Availability Checking', () => {
    it('checks availability for a date range', async () => {
      const mockAvailabilityResponse = {
        value: [
          {
            start: { dateTime: '2024-01-15T09:00:00Z' },
            end: { dateTime: '2024-01-15T10:00:00Z' }
          },
          {
            start: { dateTime: '2024-01-15T14:00:00Z' },
            end: { dateTime: '2024-01-15T15:00:00Z' }
          }
        ]
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAvailabilityResponse
      });

      const result = await service.checkAvailability({
        startDate: '2024-01-15',
        endDate: '2024-01-15',
        duration: 60,
        timezone: 'America/New_York'
      });

      expect(result).toHaveLength(2);
      expect(result[0].available).toBe(true);
      expect(result[0].start).toBe('2024-01-15T09:00:00Z');
    });

    it('filters out unavailable slots', async () => {
      const mockBusyResponse = {
        calendars: {
          'test@gmail.com': {
            busy: [
              {
                start: '2024-01-15T10:00:00Z',
                end: '2024-01-15T11:00:00Z'
              }
            ]
          }
        }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBusyResponse
      });

      const result = await service.checkAvailability({
        startDate: '2024-01-15',
        endDate: '2024-01-15',
        duration: 60,
        timezone: 'America/New_York'
      });

      const busySlot = result.find(slot =>
        slot.start === '2024-01-15T10:00:00Z'
      );

      expect(busySlot?.available).toBe(false);
    });

    it('respects business hours when checking availability', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ calendars: {} })
      });

      const result = await service.checkAvailability({
        startDate: '2024-01-15',
        endDate: '2024-01-15',
        duration: 60,
        timezone: 'America/New_York',
        businessHours: {
          start: '09:00',
          end: '17:00'
        }
      });

      // Should not include slots outside business hours
      const earlySlot = result.find(slot =>
        new Date(slot.start).getHours() < 9
      );
      const lateSlot = result.find(slot =>
        new Date(slot.start).getHours() >= 17
      );

      expect(earlySlot).toBeUndefined();
      expect(lateSlot).toBeUndefined();
    });
  });

  describe('Appointment Booking', () => {
    it('books an appointment successfully', async () => {
      const mockEventResponse = {
        id: 'event_123456',
        summary: 'Consultation with John Doe',
        start: { dateTime: '2024-01-15T10:00:00Z' },
        end: { dateTime: '2024-01-15T11:00:00Z' },
        attendees: [
          { email: 'customer@email.com', responseStatus: 'accepted' }
        ]
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockEventResponse
      });

      const booking = await service.bookAppointment({
        startTime: '2024-01-15T10:00:00Z',
        endTime: '2024-01-15T11:00:00Z',
        appointmentType: 'consultation',
        customerInfo: {
          name: 'John Doe',
          email: 'customer@email.com',
          phone: '+1234567890'
        },
        notes: 'Initial consultation'
      });

      expect(booking.id).toBe('event_123456');
      expect(booking.status).toBe('confirmed');
      expect(booking.customerInfo.name).toBe('John Doe');
    });

    it('handles booking conflicts', async () => {
      (fetch as any).mockRejectedValueOnce({
        status: 409,
        message: 'Conflict: Time slot no longer available'
      });

      await expect(service.bookAppointment({
        startTime: '2024-01-15T10:00:00Z',
        endTime: '2024-01-15T11:00:00Z',
        appointmentType: 'consultation',
        customerInfo: {
          name: 'John Doe',
          email: 'customer@email.com',
          phone: '+1234567890'
        }
      })).rejects.toThrow(/time slot no longer available/i);
    });

    it('sends confirmation email after booking', async () => {
      const mockBookingResponse = {
        id: 'event_123456',
        start: { dateTime: '2024-01-15T10:00:00Z' },
        end: { dateTime: '2024-01-15T11:00:00Z' }
      };

      const mockEmailResponse = {
        messageId: 'email_123456',
        status: 'sent'
      };

      (fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockBookingResponse
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => mockEmailResponse
        });

      const booking = await service.bookAppointment({
        startTime: '2024-01-15T10:00:00Z',
        endTime: '2024-01-15T11:00:00Z',
        appointmentType: 'consultation',
        customerInfo: {
          name: 'John Doe',
          email: 'customer@email.com',
          phone: '+1234567890'
        },
        sendConfirmation: true
      });

      expect(booking.confirmationSent).toBe(true);
    });
  });

  describe('Appointment Management', () => {
    it('reschedules an appointment', async () => {
      const mockRescheduleResponse = {
        id: 'event_123456',
        start: { dateTime: '2024-01-16T14:00:00Z' },
        end: { dateTime: '2024-01-16T15:00:00Z' },
        status: 'confirmed'
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockRescheduleResponse
      });

      const result = await service.rescheduleAppointment({
        appointmentId: 'event_123456',
        newStartTime: '2024-01-16T14:00:00Z',
        newEndTime: '2024-01-16T15:00:00Z',
        reason: 'Customer requested change'
      });

      expect(result.id).toBe('event_123456');
      expect(result.startTime).toBe('2024-01-16T14:00:00Z');
    });

    it('cancels an appointment', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'cancelled' })
      });

      const result = await service.cancelAppointment({
        appointmentId: 'event_123456',
        reason: 'Customer cancellation',
        sendNotification: true
      });

      expect(result.success).toBe(true);
      expect(result.status).toBe('cancelled');
    });

    it('gets appointment details', async () => {
      const mockAppointment = {
        id: 'event_123456',
        summary: 'Consultation',
        start: { dateTime: '2024-01-15T10:00:00Z' },
        end: { dateTime: '2024-01-15T11:00:00Z' },
        attendees: [
          { email: 'customer@email.com', displayName: 'John Doe' }
        ]
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockAppointment
      });

      const result = await service.getAppointment('event_123456');

      expect(result.id).toBe('event_123456');
      expect(result.startTime).toBe('2024-01-15T10:00:00Z');
    });
  });

  describe('VAPI Function Handling', () => {
    it('handles check_availability function', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ calendars: {} })
      });

      const result = await service.handleVAPIFunction(
        'check_availability',
        {
          date: '2024-01-15',
          duration: 60
        },
        { customerPhone: '+1234567890' }
      );

      expect(result.success).toBe(true);
      expect(Array.isArray(result.availableSlots)).toBe(true);
    });

    it('handles book_appointment function', async () => {
      const mockBooking = {
        id: 'event_123456',
        start: { dateTime: '2024-01-15T10:00:00Z' },
        end: { dateTime: '2024-01-15T11:00:00Z' }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBooking
      });

      const result = await service.handleVAPIFunction(
        'book_appointment',
        {
          startTime: '2024-01-15T10:00:00Z',
          appointmentType: 'consultation',
          customerName: 'John Doe',
          customerEmail: 'john@email.com'
        },
        { customerPhone: '+1234567890' }
      );

      expect(result.success).toBe(true);
      expect(result.appointmentId).toBe('event_123456');
    });

    it('handles reschedule_appointment function', async () => {
      const mockReschedule = {
        id: 'event_123456',
        start: { dateTime: '2024-01-16T14:00:00Z' },
        end: { dateTime: '2024-01-16T15:00:00Z' }
      };

      (fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockReschedule
      });

      const result = await service.handleVAPIFunction(
        'reschedule_appointment',
        {
          appointmentId: 'event_123456',
          newStartTime: '2024-01-16T14:00:00Z'
        },
        { customerPhone: '+1234567890' }
      );

      expect(result.success).toBe(true);
      expect(result.newStartTime).toBe('2024-01-16T14:00:00Z');
    });

    it('handles unknown function gracefully', async () => {
      const result = await service.handleVAPIFunction(
        'unknown_function',
        {},
        { customerPhone: '+1234567890' }
      );

      expect(result.error).toBe(true);
      expect(result.message).toContain('Unknown function');
    });
  });

  describe('Multiple Calendar Integration', () => {
    it('checks availability across multiple calendars', async () => {
      const multiCalendarService = new AppointmentSchedulingService([
        {
          provider: 'google',
          calendarId: 'calendar1@gmail.com',
          apiKey: 'key1',
          name: 'Calendar 1',
          primaryCalendar: true
        },
        {
          provider: 'outlook',
          calendarId: 'calendar2',
          accessToken: 'token2',
          name: 'Calendar 2',
          primaryCalendar: false
        }
      ]);

      (fetch as any)
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ calendars: {} })
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ value: [] })
        });

      const result = await multiCalendarService.checkAvailability({
        startDate: '2024-01-15',
        endDate: '2024-01-15',
        duration: 60,
        timezone: 'America/New_York'
      });

      expect(fetch).toHaveBeenCalledTimes(2);
      expect(Array.isArray(result)).toBe(true);
    });
  });

  describe('Error Handling', () => {
    it('handles API rate limiting', async () => {
      (fetch as any).mockResolvedValueOnce({
        ok: false,
        status: 429,
        statusText: 'Too Many Requests'
      });

      await expect(service.checkAvailability({
        startDate: '2024-01-15',
        endDate: '2024-01-15',
        duration: 60,
        timezone: 'America/New_York'
      })).rejects.toThrow(/too many requests/i);
    });

    it('handles network timeouts', async () => {
      (fetch as any).mockRejectedValueOnce(new Error('Network timeout'));

      await expect(service.bookAppointment({
        startTime: '2024-01-15T10:00:00Z',
        endTime: '2024-01-15T11:00:00Z',
        appointmentType: 'consultation',
        customerInfo: {
          name: 'John Doe',
          email: 'customer@email.com',
          phone: '+1234567890'
        }
      })).rejects.toThrow(/network timeout/i);
    });
  });
});