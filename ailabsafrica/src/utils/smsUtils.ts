import { supabase } from '@/integrations/supabase/client';

export interface SMSRequest {
  phone_number: string;
  message: string;
  user_id?: string;
}

export interface SMSResponse {
  success: boolean;
  message: string;
  data?: {
    phone_number: string;
    message_length: number;
    timestamp: string;
  };
  error?: string;
}

/**
 * Send an SMS message using the Vonage/Nexmo configuration in Supabase OTP
 * @param phoneNumber - The phone number in international format (e.g., +1234567890)
 * @param message - The message to send (max 160 characters)
 * @param userId - Optional user ID for logging purposes
 * @returns Promise<SMSResponse>
 */
export const sendSMS = async (
  phoneNumber: string,
  message: string,
  userId?: string
): Promise<SMSResponse> => {
  try {
    // Validate inputs
    if (!phoneNumber || !message) {
      return {
        success: false,
        message: 'Phone number and message are required',
        error: 'Missing required fields'
      };
    }

    // Validate phone number format
    const phoneRegex = /^\+?[1-9]\d{1,14}$/;
    if (!phoneRegex.test(phoneNumber.replace(/\s/g, ''))) {
      return {
        success: false,
        message: 'Invalid phone number format',
        error: 'Please use international format (e.g., +1234567890)'
      };
    }

    // Validate message length
    if (message.length > 160) {
      return {
        success: false,
        message: 'Message too long',
        error: 'SMS messages must be 160 characters or less'
      };
    }

    // Send SMS via Supabase Edge Function
    const { data, error } = await supabase.functions.invoke('send-sms', {
      body: {
        phone_number: phoneNumber.trim(),
        message: message.trim(),
        user_id: userId
      }
    });

    if (error) {
      return {
        success: false,
        message: 'Failed to send SMS',
        error: error.message
      };
    }

    return {
      success: true,
      message: 'SMS sent successfully',
      data: data?.data
    };

  } catch (error: any) {
    console.error('Error sending SMS:', error);
    return {
      success: false,
      message: 'Failed to send SMS',
      error: error.message || 'Unknown error occurred'
    };
  }
};

/**
 * Send a notification SMS (e.g., for call summaries, reminders)
 * @param phoneNumber - The phone number to send to
 * @param notificationType - Type of notification
 * @param details - Additional details for the notification
 * @param userId - Optional user ID for logging
 * @returns Promise<SMSResponse>
 */
export const sendNotificationSMS = async (
  phoneNumber: string,
  notificationType: 'call_summary' | 'reminder' | 'alert' | 'confirmation',
  details: Record<string, any>,
  userId?: string
): Promise<SMSResponse> => {
  let message = '';

  switch (notificationType) {
    case 'call_summary':
      message = `Call Summary: ${details.summary || 'Call completed'}. Duration: ${details.duration || 'N/A'}. Cost: $${details.cost || '0.00'}`;
      break;
    case 'reminder':
      message = `Reminder: ${details.title || 'You have a scheduled call'} at ${details.time || 'the scheduled time'}`;
      break;
    case 'alert':
      message = `Alert: ${details.message || 'Important notification'}`;
      break;
    case 'confirmation':
      message = `Confirmation: ${details.message || 'Action completed successfully'}`;
      break;
    default:
      message = details.message || 'Notification from AI Labs';
  }

  return sendSMS(phoneNumber, message, userId);
};

/**
 * Format phone number for display
 * @param phoneNumber - Raw phone number
 * @returns Formatted phone number
 */
export const formatPhoneNumber = (phoneNumber: string): string => {
  const cleaned = phoneNumber.replace(/\D/g, '');
  const match = cleaned.match(/^(\d{1})(\d{3})(\d{3})(\d{4})$/);
  if (match) {
    return `+${match[1]} (${match[2]}) ${match[3]}-${match[4]}`;
  }
  return phoneNumber;
};

/**
 * Validate phone number format
 * @param phoneNumber - Phone number to validate
 * @returns boolean
 */
export const isValidPhoneNumber = (phoneNumber: string): boolean => {
  const phoneRegex = /^\+?[1-9]\d{1,14}$/;
  return phoneRegex.test(phoneNumber.replace(/\s/g, ''));
};
