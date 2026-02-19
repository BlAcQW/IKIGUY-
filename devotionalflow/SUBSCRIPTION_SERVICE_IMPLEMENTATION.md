# Subscription Service Implementation

## Overview

A comprehensive subscription service has been implemented for DevotionalFlow that allows people to subscribe to daily devotionals via email, WhatsApp, or join a Facebook group. The service includes automated drip feed delivery using a scheduler.

## Features Implemented

### 1. Subscription Management

- **Email Subscriptions**: Users can subscribe with their email address
- **WhatsApp Subscriptions**: Users can subscribe with their WhatsApp number (E.164 format)
- **Facebook Group**: Users can indicate preference to join Facebook group (they join manually)
- **Verification**: Email and WhatsApp subscriptions require verification
- **Unsubscribe**: Users can unsubscribe via email, WhatsApp, or token

### 2. Drip Feed Service

- **Daily Delivery**: Automatically sends today's published devotional to all active subscribers
- **Multi-Channel**: Supports email, WhatsApp, and Facebook group notifications
- **Custom Content**: Admins can send custom content to subscribers
- **Scheduled Delivery**: Runs daily at 8:00 AM UTC via APScheduler

### 3. Admin Features

- **List Subscriptions**: View all subscriptions with pagination and filters
- **Update Subscriptions**: Modify subscription preferences
- **Manual Trigger**: Manually trigger drip feed delivery
- **Custom Content**: Send custom messages to subscribers

## API Endpoints

### Public Endpoints

#### Subscribe
```
POST /api/v1/subscribe
```
Subscribe to daily devotionals via email, WhatsApp, or Facebook group.

**Request Body:**
```json
{
  "name": "John Doe",
  "email": "john@example.com",  // Optional
  "whatsapp": "+233123456789",   // Optional (E.164 format)
  "facebook_group": true,        // Optional
  "preferences": {}              // Optional
}
```

#### Unsubscribe
```
POST /api/v1/unsubscribe
```
Unsubscribe using email, WhatsApp, or token.

**Request Body:**
```json
{
  "email": "john@example.com",  // Optional
  "whatsapp": "+233123456789",  // Optional
  "token": "unsubscribe_token"  // Optional
}
```

#### Verify Subscription
```
GET /api/v1/subscriptions/verify/{subscription_id}?channel=email&token=verification_token
```
Verify subscription channel (email or WhatsApp).

### Admin Endpoints

#### List Subscriptions
```
GET /api/v1/subscriptions?page=1&page_size=50&is_active=true&channel=email
```
Get paginated list of subscriptions with filters.

#### Get Subscription
```
GET /api/v1/subscriptions/{subscription_id}
```
Get subscription details by ID.

#### Update Subscription
```
PUT /api/v1/subscriptions/{subscription_id}
```
Update subscription preferences.

#### Send Daily Devotional
```
POST /api/v1/admin/subscriptions/drip-feed/send
```
Manually trigger drip feed delivery of today's devotional.

#### Send Custom Content
```
POST /api/v1/admin/subscriptions/drip-feed/custom?channel=email
```
Send custom content to subscribers.

**Request Body:**
```json
{
  "title": "Special Announcement",
  "body": "Content here...",
  "link": "https://example.com"
}
```

## Database Collections

### subscriptions
Stores subscription information:
- `name`: Subscriber name
- `email`: Email address (optional)
- `whatsapp`: WhatsApp number (optional)
- `facebook_group`: Facebook group preference
- `is_active`: Subscription status
- `verified_email`: Email verification status
- `verified_whatsapp`: WhatsApp verification status
- `preferences`: User preferences
- `last_sent_at`: Last content sent timestamp
- `last_sent_content_id`: Last content ID sent
- `total_sent`: Total messages sent
- `unsubscribe_token`: Token for unsubscribe links

### drip_feed_log
Logs drip feed delivery runs:
- `devotional_id`: Devotional ID (for daily runs)
- `run_at`: Run timestamp
- `stats`: Delivery statistics
- `type`: Run type (daily_devotional, custom)

## Configuration

### Environment Variables

Add to `.env` file:

```bash
# WhatsApp/Twilio (for subscription service)
TWILIO_ACCOUNT_SID=your_twilio_account_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+1234567890
```

### Dependencies

Added to `requirements.txt`:
- `apscheduler==3.10.4` - For scheduled drip feed delivery
- `twilio==9.3.7` - For WhatsApp messaging

## Scheduler

The drip feed scheduler runs automatically:
- **Schedule**: Daily at 8:00 AM UTC
- **Task**: Sends today's published devotional to all active subscribers
- **Channels**: Email, WhatsApp, Facebook group (tracking only)

The scheduler is initialized in `main.py` on application startup.

## Email Templates

### Verification Email
Sent when user subscribes with email:
- Subject: "Verify Your FreshManna Subscription"
- Includes verification link
- Includes unsubscribe link

### Daily Devotional Email
Sent daily to email subscribers:
- Subject: "FreshManna Daily Devotional: {title}"
- Includes devotional title, excerpt, and link
- Includes unsubscribe link

## WhatsApp Messages

### Verification Message
Sent when user subscribes with WhatsApp:
- Welcome message
- Verification link
- Unsubscribe instructions

### Daily Devotional Message
Sent daily to WhatsApp subscribers:
- Devotional title and excerpt
- Link to full devotional
- Unsubscribe instructions

## Facebook Group

Facebook group subscription is tracked but users join manually. The system logs when content is available for Facebook group members.

## Usage Examples

### Subscribe via Email
```bash
curl -X POST https://api.freshmanna365.com/api/v1/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com"
  }'
```

### Subscribe via WhatsApp
```bash
curl -X POST https://api.freshmanna365.com/api/v1/subscribe \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "whatsapp": "+233123456789"
  }'
```

### Unsubscribe
```bash
curl -X POST https://api.freshmanna365.com/api/v1/unsubscribe \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com"
  }'
```

### Admin: List Subscriptions
```bash
curl -X GET "https://api.freshmanna365.com/api/v1/subscriptions?page=1&page_size=50&channel=email" \
  -H "Authorization: Bearer {admin_token}"
```

### Admin: Send Custom Content
```bash
curl -X POST https://api.freshmanna365.com/api/v1/admin/subscriptions/drip-feed/custom \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Special Announcement",
    "body": "We have exciting news!",
    "link": "https://freshmanna365.com/announcement"
  }'
```

## Files Created/Modified

### New Files
1. `backend/app/models/subscription.py` - Subscription models
2. `backend/app/services/subscription_service.py` - Subscription management service
3. `backend/app/services/drip_feed_service.py` - Drip feed delivery service
4. `backend/app/routes/subscriptions.py` - Subscription API routes

### Modified Files
1. `backend/app/main.py` - Added subscription routes and scheduler
2. `backend/app/config.py` - Added Twilio/WhatsApp configuration
3. `backend/requirements.txt` - Added apscheduler and twilio dependencies

## Next Steps

### Frontend Implementation (Pending)
- Subscription form component
- Unsubscribe page
- Verification page
- Admin subscription management UI

### Enhancements
- Time zone support for scheduled delivery
- Delivery preferences (frequency, time of day)
- A/B testing for email templates
- Analytics dashboard for subscription metrics
- Batch unsubscribe management
- Subscription import/export

## Testing

To test the subscription service:

1. **Subscribe**:
   ```bash
   curl -X POST http://localhost:30037/api/v1/subscribe \
     -H "Content-Type: application/json" \
     -d '{"name": "Test User", "email": "test@example.com"}'
   ```

2. **Verify** (check email for verification link)

3. **Trigger Drip Feed** (as admin):
   ```bash
   curl -X POST http://localhost:30037/api/v1/admin/subscriptions/drip-feed/send \
     -H "Authorization: Bearer {admin_token}"
   ```

4. **Check Logs**:
   - Subscription created in `subscriptions` collection
   - Drip feed run logged in `drip_feed_log` collection

## Notes

- Email service uses the shared `UnifiedEmailService` from `apps.shared.services.unified_email_service`
- WhatsApp uses Twilio directly (not Meta WhatsApp Business API)
- Facebook group is tracking only - users join manually
- Scheduler requires APScheduler to be installed
- All timestamps are in UTC

## Status

✅ **Backend Complete**
- Subscription models
- Subscription service
- Drip feed service
- API routes
- Scheduler integration

⏳ **Frontend Pending**
- Subscription form
- Unsubscribe page
- Verification page
- Admin UI

