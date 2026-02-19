# Subscription Notification Settings

## Overview

Admins can now configure when subscribed users receive their daily devotional notifications via email and WhatsApp. The notification schedule is fully configurable through the admin settings panel.

## Features

### Admin Controls

1. **Enable/Disable Drip Feed**: Toggle subscription drip feed on/off
2. **Schedule Time**: Set the exact time (UTC) when notifications are sent daily
3. **Automatic Rescheduling**: When settings change, the scheduler automatically updates

### Settings Location

**Admin Panel → Settings → Email Tab → Subscription Drip Feed Section**

## Configuration

### Default Settings

- **Enabled**: Yes
- **Send Time**: 08:00 UTC (8:00 AM UTC)
- **Timezone**: UTC

### How to Configure

1. Navigate to **Admin → Settings → Email**
2. Scroll to **Subscription Drip Feed** section
3. Toggle **Enable Subscription Drip Feed** on/off
4. Set **Send Time (UTC)** using the time picker (24-hour format)
5. Click **Save Email Settings**

### Time Format

- Format: `HH:MM` (24-hour format)
- Example: `08:00` = 8:00 AM UTC
- Example: `14:30` = 2:30 PM UTC
- Example: `00:00` = Midnight UTC

## Technical Implementation

### Backend Changes

1. **Settings Model** (`app/models/settings.py`):
   - Added `enable_subscription_drip_feed: bool`
   - Added `subscription_drip_feed_time: str` (HH:MM format)
   - Added `subscription_drip_feed_timezone: str` (default: UTC)

2. **Scheduler** (`app/main.py`):
   - Reads schedule time from platform settings
   - Automatically reschedules when settings change
   - Checks if drip feed is enabled before sending

3. **Settings Service** (`app/services/settings_service.py`):
   - Default settings include subscription drip feed configuration
   - Settings update triggers scheduler reschedule

### Frontend Changes

1. **Admin Settings UI** (`frontend/src/pages/admin/AdminSettings.tsx`):
   - Added subscription drip feed controls to Email tab
   - Time picker for setting notification time
   - Enable/disable toggle

## API Endpoints

### Get Settings
```
GET /api/v1/admin/settings
```

Response includes:
```json
{
  "settings": {
    "notifications": {
      "enable_subscription_drip_feed": true,
      "subscription_drip_feed_time": "08:00",
      "subscription_drip_feed_timezone": "UTC"
    }
  }
}
```

### Update Settings
```
PATCH /api/v1/admin/settings
```

Request body:
```json
{
  "notifications": {
    "enable_subscription_drip_feed": true,
    "subscription_drip_feed_time": "09:00",
    "subscription_drip_feed_timezone": "UTC"
  }
}
```

When subscription settings are updated, the scheduler automatically reschedules the drip feed job.

## How It Works

1. **On Startup**: 
   - Scheduler reads settings from database
   - Schedules drip feed job at configured time

2. **When Settings Change**:
   - Admin updates settings via UI
   - Backend saves new settings
   - Scheduler automatically reschedules job with new time

3. **Daily Execution**:
   - At scheduled time, scheduler checks if drip feed is enabled
   - If enabled, sends today's devotional to all active subscribers
   - If disabled, skips execution

## Examples

### Example 1: Send at 6:00 AM UTC
1. Set `subscription_drip_feed_time` to `06:00`
2. Save settings
3. Scheduler reschedules to 6:00 AM UTC
4. Subscribers receive devotionals at 6:00 AM UTC daily

### Example 2: Disable Drip Feed
1. Toggle `enable_subscription_drip_feed` to `false`
2. Save settings
3. Scheduler stops sending (job remains but checks flag)
4. No notifications sent until re-enabled

### Example 3: Change from 8 AM to 9 PM
1. Set `subscription_drip_feed_time` to `21:00`
2. Save settings
3. Scheduler reschedules to 9:00 PM UTC
4. Subscribers now receive at 9:00 PM UTC instead of 8:00 AM

## Timezone Considerations

Currently, all times are in UTC. Future enhancements could include:
- Per-user timezone preferences
- Automatic timezone conversion
- Multiple send times for different regions

## Testing

### Test Changing Schedule Time
1. Set time to current time + 1 minute
2. Save settings
3. Wait 1 minute
4. Check logs for drip feed execution
5. Verify subscribers received notifications

### Test Disabling
1. Disable subscription drip feed
2. Save settings
3. Wait for scheduled time
4. Verify no notifications sent (check logs)

### Test Re-enabling
1. Re-enable subscription drip feed
2. Save settings
3. Verify scheduler reschedules job
4. Wait for next scheduled time
5. Verify notifications sent

## Notes

- **UTC Time**: All times are stored and executed in UTC
- **Immediate Effect**: Changes take effect immediately (scheduler reschedules)
- **No Restart Required**: Changes apply without restarting the server
- **Backward Compatible**: Existing subscriptions continue to work
- **Manual Override**: Admins can still manually trigger drip feed via API

## Future Enhancements

1. **Per-User Time Preferences**: Allow users to set their preferred notification time
2. **Timezone Support**: Convert UTC time to user's local timezone
3. **Multiple Send Times**: Send at different times for different regions
4. **Scheduling UI**: Visual calendar for scheduling
5. **Delivery Reports**: Track when notifications were sent
6. **A/B Testing**: Test different send times for engagement

