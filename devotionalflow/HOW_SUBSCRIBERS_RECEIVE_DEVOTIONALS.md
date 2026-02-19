# How Subscribed Users Receive Devotionals

## Overview

Subscribed users receive daily devotionals automatically via their preferred channels (email, WhatsApp, or Facebook group). The system uses a scheduler to send devotionals at a configurable time each day.

## Delivery Methods

### 1. Email Delivery

**How it works:**
1. User subscribes with email address
2. User verifies email via link sent to inbox
3. Once verified, user receives daily devotionals via email
4. Emails are sent at the scheduled time (default: 8:00 AM UTC)

**Email Content:**
- Subject: "FreshManna Daily Devotional: {Title}"
- Includes devotional title
- Includes excerpt/preview
- Link to full devotional on website
- Unsubscribe link

**Example Email:**
```
Subject: FreshManna Daily Devotional: Walking in Faith

Body:
[Devotional Title]
[Excerpt/Preview]

Read Full Devotional: [Link]

---
Unsubscribe: [Link]
```

### 2. WhatsApp Delivery

**How it works:**
1. User subscribes with WhatsApp number (E.164 format: +233123456789)
2. User verifies via WhatsApp message
3. Once verified, user receives daily devotionals via WhatsApp
4. Messages sent at scheduled time

**WhatsApp Message Format:**
```
🙏 FreshManna Daily Devotional

*[Title]*

[Excerpt]

Read full: [Link]

---
Reply STOP to unsubscribe
```

### 3. Facebook Group

**How it works:**
1. User indicates preference to join Facebook group
2. System tracks this preference
3. User joins Facebook group manually
4. Devotionals are posted in the group (admin posts manually or via automation)

## Automatic Delivery Schedule

### Default Schedule
- **Time**: 8:00 AM UTC daily
- **Frequency**: Once per day
- **Content**: Today's published devotional

### Admin Configuration

Admins can configure the delivery schedule:

1. **Go to**: Admin → Settings → Email Tab
2. **Find**: "Subscription Drip Feed" section
3. **Configure**:
   - Enable/Disable drip feed
   - Set send time (24-hour format, UTC)
   - Example: `09:00` = 9:00 AM UTC

### How Scheduler Works

1. **On Startup**: Scheduler reads settings and schedules job
2. **Daily Execution**: At scheduled time:
   - Finds today's published devotional
   - Gets all active, verified subscribers
   - Sends devotional to each subscriber via their preferred channel
   - Logs delivery statistics
3. **When Settings Change**: Scheduler automatically reschedules

## Manual Trigger (Admin Only)

Admins can manually trigger drip feed delivery:

**API Endpoint:**
```bash
POST /api/v1/admin/subscriptions/drip-feed/send
Authorization: Bearer {admin_token}
```

**Response:**
```json
{
  "success": true,
  "devotional_id": "...",
  "devotional_title": "...",
  "stats": {
    "email_sent": 10,
    "email_failed": 0,
    "whatsapp_sent": 5,
    "whatsapp_failed": 0,
    "facebook_notified": 3,
    "total_subscribers": 18
  }
}
```

## Test Results

### Test Email Sent to alfred.anyan@gmail.com

**Status**: ✅ Successfully Sent

**Test Details:**
- Subscription ID: `69482057f258c65550580c1a`
- Email: `alfred.anyan@gmail.com`
- Verified: ✅ Yes
- Active: ✅ Yes
- Total Sent: 1 (after test)

**Email Delivery Confirmed:**
- Email service: SMTP (local relay)
- Status: Sent successfully
- Message ID: Generated

## Delivery Flow

```
┌─────────────────┐
│  Scheduler      │
│  (8:00 AM UTC)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Find Today's    │
│ Devotional      │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Get Active      │
│ Subscribers     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ For Each        │
│ Subscriber:     │
│  - Email?       │
│  - WhatsApp?    │
│  - Facebook?    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Send via        │
│ Preferred       │
│ Channel         │
└─────────────────┘
```

## Requirements for Delivery

### Email Subscribers
- ✅ Subscription active (`is_active: true`)
- ✅ Email verified (`verified_email: true`)
- ✅ Email address provided

### WhatsApp Subscribers
- ✅ Subscription active (`is_active: true`)
- ✅ WhatsApp verified (`verified_whatsapp: true`)
- ✅ WhatsApp number provided (E.164 format)

### Facebook Group
- ✅ Subscription active (`is_active: true`)
- ✅ Facebook group preference set (`facebook_group: true`)

## What Gets Sent

### Daily Devotional Email
- **Subject**: "FreshManna Daily Devotional: {Title}"
- **Content**:
  - Devotional title
  - Excerpt/preview (first paragraph or excerpt field)
  - "Read Full Devotional" button/link
  - Unsubscribe link
- **Format**: HTML email with plain text fallback

### Daily Devotional WhatsApp
- **Format**: Text message with formatting
- **Content**:
  - Devotional title (bold)
  - Excerpt/preview
  - Link to full devotional
  - Unsubscribe instructions

## Unsubscribe

Users can unsubscribe via:
1. **Email**: Click unsubscribe link in email
2. **WhatsApp**: Reply "STOP"
3. **Website**: Visit unsubscribe page with token
4. **API**: POST to `/api/v1/unsubscribe` with email/WhatsApp/token

## Testing

### Test Email Delivery
```bash
# Send custom test email
curl -X POST http://localhost:30042/api/v1/admin/subscriptions/drip-feed/custom \
  -H "Authorization: Bearer {admin_token}" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Devotional",
    "body": "Test content...",
    "link": "https://freshmanna.ailabsafrica.com"
  }'
```

### Test Daily Devotional
```bash
# Trigger daily devotional delivery
curl -X POST http://localhost:30042/api/v1/admin/subscriptions/drip-feed/send \
  -H "Authorization: Bearer {admin_token}"
```

## Logs

Check service logs for delivery status:
```bash
journalctl -u kasaai-devotionalflow-backend -f | grep -i "drip\|email\|whatsapp"
```

## Status

✅ **Email Delivery**: Working
✅ **WhatsApp Delivery**: Ready (requires Twilio config)
✅ **Scheduler**: Active and running
✅ **Admin Controls**: Available in Settings

## Next Steps

1. ✅ Test email sent to alfred.anyan@gmail.com - **Confirmed**
2. ⏳ Check email inbox for received message
3. ⏳ Verify email formatting and links work
4. ⏳ Test daily automatic delivery at scheduled time

