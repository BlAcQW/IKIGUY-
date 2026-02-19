# SMS Integration with Vonage/Nexmo

This document describes the SMS integration feature that allows sending SMS messages using Vonage (formerly Nexmo) through Supabase's OTP configuration.

## Overview

The SMS integration provides:
- Direct SMS sending via Supabase Edge Functions
- Integration with Vonage/Nexmo using Supabase's OTP configuration
- Phone number validation and formatting
- Message length validation (160 character limit)
- Action logging for analytics
- Utility functions for easy integration

## API Endpoint

### `POST /functions/v1/send-sms`

Sends an SMS message to a specified phone number.

**Request Body:**
```json
{
  "phone_number": "+1234567890",
  "message": "Your message here",
  "user_id": "optional-user-id-for-logging"
}
```

**Response:**
```json
{
  "success": true,
  "message": "SMS sent successfully",
  "data": {
    "phone_number": "+1234567890",
    "message_length": 20,
    "timestamp": "2025-01-21T10:30:00.000Z"
  }
}
```

## Frontend Integration

### Using the Utility Function

```typescript
import { sendSMS, sendNotificationSMS } from '@/utils/smsUtils';

// Send a custom message
const result = await sendSMS(
  '+1234567890',
  'Hello from AI Labs!',
  user.id
);

// Send a notification
const notificationResult = await sendNotificationSMS(
  '+1234567890',
  'call_summary',
  {
    summary: 'Call completed successfully',
    duration: '5 minutes',
    cost: '0.50'
  },
  user.id
);
```

### Using the SMS Tester Component

The SMS Tester is available in the dashboard under the "SMS Tester" tab. It provides:
- Phone number input with validation
- Message input with character counter
- Real-time validation
- Success/error feedback

## Configuration

### Supabase Setup

1. **Enable SMS in Supabase Auth:**
   - Go to Authentication > Settings > SMS
   - Enable SMS provider
   - Configure Vonage/Nexmo credentials

2. **Vonage/Nexmo Configuration:**
   - API Key
   - API Secret
   - From number (your Vonage number)

3. **Edge Function Configuration:**
   - The `send-sms` function is configured to not require JWT verification
   - Uses Supabase's built-in SMS functionality

### Environment Variables

Ensure these are set in your Supabase project:
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- Vonage credentials (configured in Supabase Auth settings)

## Usage Examples

### 1. Call Summary Notifications

```typescript
// After a call ends, send summary
await sendNotificationSMS(
  userPhoneNumber,
  'call_summary',
  {
    summary: callSummary,
    duration: callDuration,
    cost: callCost
  },
  userId
);
```

### 2. Appointment Reminders

```typescript
// Send appointment reminder
await sendNotificationSMS(
  customerPhone,
  'reminder',
  {
    title: 'Appointment Reminder',
    time: '2:00 PM today'
  },
  userId
);
```

### 3. Custom Messages

```typescript
// Send custom message
await sendSMS(
  phoneNumber,
  'Your order has been shipped!',
  userId
);
```

## Validation

### Phone Number Validation
- Must be in international format
- Supports +1 (country code) format
- Validates against E.164 standard
- Removes spaces and special characters

### Message Validation
- Maximum 160 characters
- Trims whitespace
- Validates required fields

## Error Handling

The system provides comprehensive error handling:

```typescript
const result = await sendSMS(phoneNumber, message, userId);

if (result.success) {
  // SMS sent successfully
  console.log('SMS sent:', result.data);
} else {
  // Handle error
  console.error('SMS failed:', result.error);
}
```

## Logging and Analytics

All SMS actions are logged to the `assistant_actions` table with:
- User ID (if provided)
- Action type: 'send_sms'
- Details including phone number, message, and timestamp
- Created timestamp

## Security Considerations

1. **Rate Limiting:** Consider implementing rate limiting for SMS sending
2. **Phone Number Validation:** Always validate phone numbers before sending
3. **Message Content:** Validate message content for appropriate use
4. **User Permissions:** Ensure users have permission to send SMS
5. **Cost Monitoring:** Monitor SMS costs and usage

## Troubleshooting

### Common Issues

1. **"Invalid phone number format"**
   - Ensure phone number is in international format (+1234567890)
   - Remove spaces and special characters

2. **"Message too long"**
   - SMS messages must be 160 characters or less
   - Consider splitting long messages

3. **"Failed to send SMS"**
   - Check Vonage/Nexmo configuration in Supabase
   - Verify API credentials
   - Check account balance

4. **"Missing required fields"**
   - Ensure both phone_number and message are provided
   - Check for empty or null values

### Debugging

Enable debug logging by checking the Supabase Edge Function logs:
- Go to Supabase Dashboard > Edge Functions > Logs
- Look for `[send-sms]` log entries
- Check for error messages and stack traces

## Testing

Use the SMS Tester component in the dashboard to:
- Test phone number validation
- Test message sending
- Verify error handling
- Check response formats

## Future Enhancements

Potential improvements:
- Bulk SMS sending
- SMS templates
- Delivery status tracking
- Cost optimization
- Integration with other messaging platforms
