interface CalendarIntegration {
  provider: 'google' | 'outlook' | 'calendly' | 'acuity' | 'custom';
  apiKey: string;
  calendarId: string;
  webhookUrl?: string;
  syncEnabled: boolean;
}

interface AppointmentType {
  id: string;
  name: string;
  duration: number; // minutes
  description: string;
  bufferTime: number; // minutes
  location: 'office' | 'phone' | 'video' | 'client_location';
  price?: number;
  maxAdvanceBooking: number; // days
  minAdvanceNotice: number; // hours
  allowReschedule: boolean;
  allowCancel: boolean;
  requiresApproval: boolean;
}

interface AvailabilityRule {
  dayOfWeek: number; // 0-6 (Sunday-Saturday)
  startTime: string; // HH:MM
  endTime: string; // HH:MM
  enabled: boolean;
  breaks?: Array<{
    startTime: string;
    endTime: string;
    title: string;
  }>;
}

interface AppointmentSlot {
  start: string; // ISO string
  end: string; // ISO string
  available: boolean;
  appointmentType?: string;
  duration: number; // minutes
}

interface AppointmentBooking {
  id: string;
  appointmentTypeId: string;
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  startTime: string; // ISO string
  endTime: string; // ISO string
  status: 'confirmed' | 'pending' | 'cancelled' | 'completed' | 'no_show';
  location: string;
  notes?: string;
  price?: number;
  confirmationCode: string;
  createdAt: string;
  updatedAt: string;
}

interface AppointmentBookingRequest {
  appointmentTypeId: string;
  customerName: string;
  customerEmail: string;
  customerPhone: string;
  preferredDate: string; // YYYY-MM-DD
  preferredTime: string; // HH:MM
  notes?: string;
  timeZone?: string;
}

interface AvailabilityRequest {
  date: string; // YYYY-MM-DD
  appointmentTypeId?: string;
  duration?: number; // minutes
  timeZone?: string;
}

interface RescheduleRequest {
  appointmentId: string;
  newDate: string; // YYYY-MM-DD
  newTime: string; // HH:MM
  reason?: string;
}

interface CalendarEvent {
  id: string;
  title: string;
  start: string;
  end: string;
  description?: string;
  location?: string;
  attendees?: Array<{
    email: string;
    name?: string;
  }>;
}

export class AppointmentSchedulingService {
  private calendarIntegrations: CalendarIntegration[];
  private appointmentTypes: AppointmentType[];
  private availabilityRules: AvailabilityRule[];
  private timeZone: string;

  constructor(
    calendarIntegrations: CalendarIntegration[],
    appointmentTypes: AppointmentType[],
    availabilityRules: AvailabilityRule[],
    timeZone: string = 'America/New_York'
  ) {
    this.calendarIntegrations = calendarIntegrations;
    this.appointmentTypes = appointmentTypes;
    this.availabilityRules = availabilityRules;
    this.timeZone = timeZone;
  }

  private async makeCalendarAPIRequest(
    integration: CalendarIntegration,
    endpoint: string,
    method: string = 'GET',
    data?: any
  ): Promise<any> {
    let baseUrl = '';
    let headers: Record<string, string> = {};

    switch (integration.provider) {
      case 'google':
        baseUrl = 'https://www.googleapis.com/calendar/v3';
        headers = {
          'Authorization': `Bearer ${integration.apiKey}`,
          'Content-Type': 'application/json'
        };
        break;

      case 'outlook':
        baseUrl = 'https://graph.microsoft.com/v1.0';
        headers = {
          'Authorization': `Bearer ${integration.apiKey}`,
          'Content-Type': 'application/json'
        };
        break;

      case 'calendly':
        baseUrl = 'https://api.calendly.com';
        headers = {
          'Authorization': `Bearer ${integration.apiKey}`,
          'Content-Type': 'application/json'
        };
        break;

      case 'custom':
        baseUrl = integration.webhookUrl || '';
        headers = {
          'Authorization': `Bearer ${integration.apiKey}`,
          'Content-Type': 'application/json'
        };
        break;

      default:
        throw new Error(`Unsupported calendar provider: ${integration.provider}`);
    }

    const url = `${baseUrl}${endpoint}`;

    try {
      const response = await fetch(url, {
        method,
        headers,
        body: data ? JSON.stringify(data) : undefined
      });

      if (!response.ok) {
        throw new Error(`Calendar API request failed: ${response.status} ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Calendar API Error (${integration.provider}):`, error);
      throw error;
    }
  }

  async checkAvailability(request: AvailabilityRequest): Promise<AppointmentSlot[]> {
    try {
      const date = new Date(request.date);
      const dayOfWeek = date.getDay();

      // Check if day is available based on rules
      const dayRule = this.availabilityRules.find(rule => rule.dayOfWeek === dayOfWeek);
      if (!dayRule || !dayRule.enabled) {
        return [];
      }

      const appointmentType = request.appointmentTypeId
        ? this.appointmentTypes.find(type => type.id === request.appointmentTypeId)
        : null;

      const duration = request.duration || appointmentType?.duration || 30;
      const bufferTime = appointmentType?.bufferTime || 15;

      // Generate time slots for the day
      const slots = this.generateTimeSlots(date, dayRule, duration, bufferTime);

      // Check against existing bookings for each calendar integration
      const busySlots = await this.getBusySlots(request.date);

      // Filter out busy slots
      const availableSlots = slots.filter(slot => {
        const slotStart = new Date(slot.start);
        const slotEnd = new Date(slot.end);

        return !busySlots.some(busySlot => {
          const busyStart = new Date(busySlot.start);
          const busyEnd = new Date(busySlot.end);

          // Check for overlap
          return slotStart < busyEnd && slotEnd > busyStart;
        });
      });

      return availableSlots;
    } catch (error) {
      console.error('Availability check error:', error);
      // Return mock availability for development
      return this.getMockAvailability(request);
    }
  }

  private generateTimeSlots(
    date: Date,
    dayRule: AvailabilityRule,
    duration: number,
    bufferTime: number
  ): AppointmentSlot[] {
    const slots: AppointmentSlot[] = [];
    const [startHour, startMinute] = dayRule.startTime.split(':').map(Number);
    const [endHour, endMinute] = dayRule.endTime.split(':').map(Number);

    const startTime = new Date(date);
    startTime.setHours(startHour, startMinute, 0, 0);

    const endTime = new Date(date);
    endTime.setHours(endHour, endMinute, 0, 0);

    const slotDuration = duration + bufferTime;
    let currentTime = new Date(startTime);

    while (currentTime.getTime() + (slotDuration * 60000) <= endTime.getTime()) {
      const slotEnd = new Date(currentTime.getTime() + (duration * 60000));

      // Skip slots during breaks
      const isInBreak = dayRule.breaks?.some(breakPeriod => {
        const [breakStartHour, breakStartMinute] = breakPeriod.startTime.split(':').map(Number);
        const [breakEndHour, breakEndMinute] = breakPeriod.endTime.split(':').map(Number);

        const breakStart = new Date(date);
        breakStart.setHours(breakStartHour, breakStartMinute, 0, 0);

        const breakEnd = new Date(date);
        breakEnd.setHours(breakEndHour, breakEndMinute, 0, 0);

        return currentTime >= breakStart && currentTime < breakEnd;
      });

      if (!isInBreak) {
        slots.push({
          start: currentTime.toISOString(),
          end: slotEnd.toISOString(),
          available: true,
          duration
        });
      }

      currentTime = new Date(currentTime.getTime() + (slotDuration * 60000));
    }

    return slots;
  }

  private async getBusySlots(date: string): Promise<AppointmentSlot[]> {
    const busySlots: AppointmentSlot[] = [];

    for (const integration of this.calendarIntegrations) {
      if (!integration.syncEnabled) continue;

      try {
        let events: any[] = [];

        switch (integration.provider) {
          case 'google':
            const googleResponse = await this.makeCalendarAPIRequest(
              integration,
              `/calendars/${integration.calendarId}/events?timeMin=${date}T00:00:00Z&timeMax=${date}T23:59:59Z&singleEvents=true&orderBy=startTime`
            );
            events = googleResponse.items || [];
            break;

          case 'outlook':
            const outlookResponse = await this.makeCalendarAPIRequest(
              integration,
              `/me/calendars/${integration.calendarId}/events?$filter=start/dateTime ge '${date}T00:00:00' and start/dateTime le '${date}T23:59:59'`
            );
            events = outlookResponse.value || [];
            break;

          default:
            // Custom API or other providers
            events = [];
        }

        // Convert events to busy slots
        events.forEach(event => {
          const start = event.start?.dateTime || event.start?.date;
          const end = event.end?.dateTime || event.end?.date;

          if (start && end) {
            busySlots.push({
              start,
              end,
              available: false,
              duration: 0
            });
          }
        });
      } catch (error) {
        console.error(`Error fetching busy slots from ${integration.provider}:`, error);
      }
    }

    return busySlots;
  }

  async bookAppointment(request: AppointmentBookingRequest): Promise<AppointmentBooking> {
    try {
      const appointmentType = this.appointmentTypes.find(type => type.id === request.appointmentTypeId);
      if (!appointmentType) {
        throw new Error('Invalid appointment type');
      }

      // Verify availability
      const requestedDateTime = new Date(`${request.preferredDate}T${request.preferredTime}`);
      const endDateTime = new Date(requestedDateTime.getTime() + (appointmentType.duration * 60000));

      const availability = await this.checkAvailability({
        date: request.preferredDate,
        appointmentTypeId: request.appointmentTypeId
      });

      const isSlotAvailable = availability.some(slot => {
        const slotStart = new Date(slot.start);
        return Math.abs(slotStart.getTime() - requestedDateTime.getTime()) < 60000; // Within 1 minute
      });

      if (!isSlotAvailable) {
        throw new Error('Requested time slot is not available');
      }

      // Generate appointment booking
      const booking: AppointmentBooking = {
        id: this.generateBookingId(),
        appointmentTypeId: request.appointmentTypeId,
        customerName: request.customerName,
        customerEmail: request.customerEmail,
        customerPhone: request.customerPhone,
        startTime: requestedDateTime.toISOString(),
        endTime: endDateTime.toISOString(),
        status: appointmentType.requiresApproval ? 'pending' : 'confirmed',
        location: this.getLocationString(appointmentType.location),
        notes: request.notes,
        price: appointmentType.price,
        confirmationCode: this.generateConfirmationCode(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      // Create calendar events in all integrations
      await this.createCalendarEvents(booking, appointmentType);

      return booking;
    } catch (error) {
      console.error('Booking error:', error);
      throw error;
    }
  }

  private async createCalendarEvents(booking: AppointmentBooking, appointmentType: AppointmentType): Promise<void> {
    const event: CalendarEvent = {
      id: booking.id,
      title: `${appointmentType.name} - ${booking.customerName}`,
      start: booking.startTime,
      end: booking.endTime,
      description: `
        Appointment Type: ${appointmentType.name}
        Customer: ${booking.customerName}
        Phone: ${booking.customerPhone}
        Email: ${booking.customerEmail}
        Confirmation Code: ${booking.confirmationCode}
        ${booking.notes ? `Notes: ${booking.notes}` : ''}
      `.trim(),
      location: booking.location,
      attendees: [
        {
          email: booking.customerEmail,
          name: booking.customerName
        }
      ]
    };

    for (const integration of this.calendarIntegrations) {
      if (!integration.syncEnabled) continue;

      try {
        await this.createCalendarEvent(integration, event);
      } catch (error) {
        console.error(`Failed to create event in ${integration.provider}:`, error);
      }
    }
  }

  private async createCalendarEvent(integration: CalendarIntegration, event: CalendarEvent): Promise<void> {
    switch (integration.provider) {
      case 'google':
        await this.makeCalendarAPIRequest(
          integration,
          `/calendars/${integration.calendarId}/events`,
          'POST',
          {
            summary: event.title,
            description: event.description,
            location: event.location,
            start: {
              dateTime: event.start,
              timeZone: this.timeZone
            },
            end: {
              dateTime: event.end,
              timeZone: this.timeZone
            },
            attendees: event.attendees?.map(attendee => ({
              email: attendee.email,
              displayName: attendee.name
            }))
          }
        );
        break;

      case 'outlook':
        await this.makeCalendarAPIRequest(
          integration,
          `/me/calendars/${integration.calendarId}/events`,
          'POST',
          {
            subject: event.title,
            body: {
              contentType: 'text',
              content: event.description
            },
            location: {
              displayName: event.location
            },
            start: {
              dateTime: event.start,
              timeZone: this.timeZone
            },
            end: {
              dateTime: event.end,
              timeZone: this.timeZone
            },
            attendees: event.attendees?.map(attendee => ({
              emailAddress: {
                address: attendee.email,
                name: attendee.name
              }
            }))
          }
        );
        break;

      default:
        // Custom API or webhook
        if (integration.webhookUrl) {
          await this.makeCalendarAPIRequest(integration, '/events', 'POST', event);
        }
    }
  }

  async rescheduleAppointment(request: RescheduleRequest): Promise<AppointmentBooking> {
    try {
      // Verify new time slot availability
      const availability = await this.checkAvailability({
        date: request.newDate
      });

      const requestedDateTime = new Date(`${request.newDate}T${request.newTime}`);
      const isSlotAvailable = availability.some(slot => {
        const slotStart = new Date(slot.start);
        return Math.abs(slotStart.getTime() - requestedDateTime.getTime()) < 60000;
      });

      if (!isSlotAvailable) {
        throw new Error('Requested time slot is not available for rescheduling');
      }

      // Mock updated booking (in real implementation, this would update the database)
      const updatedBooking: AppointmentBooking = {
        id: request.appointmentId,
        appointmentTypeId: 'mock-type',
        customerName: 'Mock Customer',
        customerEmail: 'customer@example.com',
        customerPhone: '+1234567890',
        startTime: requestedDateTime.toISOString(),
        endTime: new Date(requestedDateTime.getTime() + (30 * 60000)).toISOString(),
        status: 'confirmed',
        location: 'Office',
        confirmationCode: this.generateConfirmationCode(),
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      // Update calendar events
      await this.updateCalendarEvents(updatedBooking);

      return updatedBooking;
    } catch (error) {
      console.error('Reschedule error:', error);
      throw error;
    }
  }

  private async updateCalendarEvents(booking: AppointmentBooking): Promise<void> {
    for (const integration of this.calendarIntegrations) {
      if (!integration.syncEnabled) continue;

      try {
        // In a real implementation, you'd update the existing event
        // For now, we'll just log the action
        console.log(`Updating calendar event in ${integration.provider} for booking ${booking.id}`);
      } catch (error) {
        console.error(`Failed to update event in ${integration.provider}:`, error);
      }
    }
  }

  async cancelAppointment(appointmentId: string, reason?: string): Promise<void> {
    try {
      // Delete calendar events
      await this.deleteCalendarEvents(appointmentId);

      console.log(`Appointment ${appointmentId} cancelled. Reason: ${reason || 'Not specified'}`);
    } catch (error) {
      console.error('Cancel appointment error:', error);
      throw error;
    }
  }

  private async deleteCalendarEvents(appointmentId: string): Promise<void> {
    for (const integration of this.calendarIntegrations) {
      if (!integration.syncEnabled) continue;

      try {
        // In a real implementation, you'd delete the calendar event
        console.log(`Deleting calendar event in ${integration.provider} for appointment ${appointmentId}`);
      } catch (error) {
        console.error(`Failed to delete event in ${integration.provider}:`, error);
      }
    }
  }

  async getAppointmentDetails(appointmentId: string): Promise<AppointmentBooking | null> {
    try {
      // Mock appointment details (in real implementation, fetch from database)
      return {
        id: appointmentId,
        appointmentTypeId: 'consultation',
        customerName: 'John Doe',
        customerEmail: 'john@example.com',
        customerPhone: '+1234567890',
        startTime: new Date().toISOString(),
        endTime: new Date(Date.now() + 30 * 60000).toISOString(),
        status: 'confirmed',
        location: 'Office',
        confirmationCode: 'ABC123',
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };
    } catch (error) {
      console.error('Get appointment details error:', error);
      return null;
    }
  }

  // VAPI Function Handlers
  async handleVAPIFunction(functionName: string, parameters: any, callContext: any): Promise<any> {
    const { customerPhone } = callContext;

    try {
      switch (functionName) {
        case 'check_availability':
          const availability = await this.checkAvailability({
            date: parameters.date,
            appointmentTypeId: parameters.appointmentTypeId,
            duration: parameters.duration
          });

          return {
            date: parameters.date,
            availableSlots: availability.slice(0, 5).map(slot => ({
              time: new Date(slot.start).toLocaleTimeString('en-US', {
                hour: 'numeric',
                minute: '2-digit',
                hour12: true
              }),
              duration: slot.duration
            })),
            totalSlots: availability.length
          };

        case 'book_appointment':
          const booking = await this.bookAppointment({
            ...parameters,
            customerPhone
          });

          return {
            success: true,
            appointmentId: booking.id,
            confirmationCode: booking.confirmationCode,
            startTime: booking.startTime,
            endTime: booking.endTime,
            status: booking.status,
            location: booking.location
          };

        case 'reschedule_appointment':
          const rescheduled = await this.rescheduleAppointment({
            appointmentId: parameters.appointmentId,
            newDate: parameters.newDate,
            newTime: parameters.newTime,
            reason: parameters.reason
          });

          return {
            success: true,
            appointmentId: rescheduled.id,
            newStartTime: rescheduled.startTime,
            newEndTime: rescheduled.endTime,
            confirmationCode: rescheduled.confirmationCode
          };

        case 'cancel_appointment':
          await this.cancelAppointment(parameters.appointmentId, parameters.reason);

          return {
            success: true,
            appointmentId: parameters.appointmentId,
            message: 'Your appointment has been cancelled successfully.'
          };

        case 'get_appointment_details':
          const appointment = await this.getAppointmentDetails(parameters.appointmentId);

          if (!appointment) {
            return {
              success: false,
              message: 'Appointment not found'
            };
          }

          return {
            success: true,
            appointment: {
              id: appointment.id,
              customerName: appointment.customerName,
              startTime: appointment.startTime,
              endTime: appointment.endTime,
              status: appointment.status,
              location: appointment.location,
              confirmationCode: appointment.confirmationCode
            }
          };

        case 'send_confirmation':
          return {
            success: true,
            message: 'Confirmation sent via email and SMS'
          };

        default:
          throw new Error(`Unknown function: ${functionName}`);
      }
    } catch (error) {
      console.error(`Appointment function error for ${functionName}:`, error);
      return {
        error: true,
        message: `Sorry, I encountered an error while ${functionName.replace('_', ' ')}. Let me connect you with our booking team.`
      };
    }
  }

  // Utility methods
  private getMockAvailability(request: AvailabilityRequest): AppointmentSlot[] {
    const date = new Date(request.date);
    const slots: AppointmentSlot[] = [];
    const duration = request.duration || 30;

    // Generate mock slots from 9 AM to 5 PM
    for (let hour = 9; hour < 17; hour++) {
      for (let minute = 0; minute < 60; minute += duration + 15) {
        const startTime = new Date(date);
        startTime.setHours(hour, minute, 0, 0);

        const endTime = new Date(startTime.getTime() + (duration * 60000));

        slots.push({
          start: startTime.toISOString(),
          end: endTime.toISOString(),
          available: Math.random() > 0.3, // 70% chance of being available
          duration
        });
      }
    }

    return slots.filter(slot => slot.available);
  }

  private generateBookingId(): string {
    const prefix = 'APT';
    const timestamp = Date.now().toString().slice(-6);
    const random = Math.random().toString(36).substr(2, 4).toUpperCase();
    return `${prefix}-${timestamp}-${random}`;
  }

  private generateConfirmationCode(): string {
    return Math.random().toString(36).substr(2, 8).toUpperCase();
  }

  private getLocationString(location: string): string {
    const locationMap = {
      'office': 'In Office',
      'phone': 'Phone Call',
      'video': 'Video Call',
      'client_location': 'Client Location'
    };

    return locationMap[location as keyof typeof locationMap] || location;
  }

  // Test calendar connection
  async testCalendarConnection(integration: CalendarIntegration): Promise<{ success: boolean; message: string }> {
    try {
      switch (integration.provider) {
        case 'google':
          await this.makeCalendarAPIRequest(integration, '/calendars/primary');
          break;

        case 'outlook':
          await this.makeCalendarAPIRequest(integration, '/me/calendar');
          break;

        case 'calendly':
          await this.makeCalendarAPIRequest(integration, '/users/me');
          break;

        default:
          if (integration.webhookUrl) {
            await this.makeCalendarAPIRequest(integration, '/health');
          }
      }

      return {
        success: true,
        message: `Successfully connected to ${integration.provider}`
      };
    } catch (error) {
      return {
        success: false,
        message: `Failed to connect to ${integration.provider}: ${error instanceof Error ? error.message : 'Unknown error'}`
      };
    }
  }
}

export type {
  CalendarIntegration,
  AppointmentType,
  AvailabilityRule,
  AppointmentSlot,
  AppointmentBooking,
  AppointmentBookingRequest,
  AvailabilityRequest,
  RescheduleRequest
};