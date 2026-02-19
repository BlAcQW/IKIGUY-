# Wallet Notification System - Usage Guide

## Overview

The notification system provides email and SMS notifications for wallet events including transactions, security alerts, and balance notifications.

## Features

- ✅ Email notifications (via Resend)
- ✅ SMS notifications (via Twilio)
- ✅ User notification preferences
- ✅ Multiple notification types
- ✅ Automatic retry on failure
- ✅ Notification history tracking
- ✅ Priority-based delivery

## Installation

The notification system is included in the wallet library. No additional installation required.

## Quick Start

### 1. Initialize NotificationService

```python
from motor.motor_asyncio import AsyncIOMotorClient
from apps.shared.integration.wallet import NotificationService, WalletService

# Initialize MongoDB
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.kasaai_core

# Initialize NotificationService
notification_service = NotificationService(
    database=db,
    resend_api_key="re_xxxxx",  # Your Resend API key
    twilio_config={
        "account_sid": "ACxxxxx",
        "auth_token": "xxxxx",
    },
    from_email="notifications@yourdomain.com",
    from_phone="+1234567890",
)

# Initialize WalletService with notifications
wallet_service = WalletService(
    database=db,
    notification_service=notification_service
)
```

### 2. Configure User Notification Preferences

```python
# Update user's notification preferences
await notification_service.update_user_preferences(
    user_id="user123",
    preferences_update={
        "email_enabled": True,
        "sms_enabled": True,
        "email": "user@example.com",
        "phone_number": "+1234567890",
        "transaction_notifications": True,
        "security_notifications": True,
        "balance_notifications": True,
    }
)
```

### 3. Notifications are Automatic

When using `WalletService` with `notification_service` configured, notifications are sent automatically:

```python
# This will automatically send a notification when the deposit completes
transaction, payment_result = await wallet_service.deposit(
    wallet_id="wallet123",
    amount=Decimal("100.00"),
    payment_provider=PaymentProvider.STRIPE,
    payment_method_id="pm_123"
)

# Webhook processing will trigger notifications automatically
await wallet_service.process_deposit_success(
    transaction_id=transaction.id,
    provider_transaction_id="ch_123"
)
# ✅ User receives email: "Transaction Completed - 100.00 USD"
```

## Notification Types

### Transaction Notifications

```python
# Automatically sent by WalletService:
- TRANSACTION_COMPLETED    # Deposit/withdrawal completed
- DEPOSIT_COMPLETED        # Deposit successful
- WITHDRAWAL_COMPLETED     # Withdrawal successful
- TRANSACTION_FAILED       # Transaction failed
- TRANSACTION_PENDING      # Transaction pending
```

### Balance Notifications

```python
# Send low balance alert
await notification_service.notify_low_balance(
    wallet=wallet,
    threshold=Decimal("20.00")
)
```

### Security Notifications

```python
# Send suspicious activity alert
await notification_service.notify_suspicious_activity(
    wallet=wallet,
    reason="Multiple failed login attempts"
)
# ✅ Sends URGENT notification via both email AND SMS
```

### Manual Notifications

```python
from apps.shared.integration.wallet import (
    NotificationType,
    NotificationPriority,
    NotificationChannel
)

# Send custom notification
await notification_service.send_notification(
    user_id="user123",
    notification_type=NotificationType.SECURITY_ALERT,
    subject="Important Security Update",
    message="Your account password was changed.",
    html_message="<h2>Password Changed</h2><p>Your password was updated.</p>",
    priority=NotificationPriority.HIGH,
    channel=NotificationChannel.EMAIL,
)
```

## User Preferences Management

### Get User Preferences

```python
prefs = await notification_service.get_user_preferences("user123")

print(f"Email enabled: {prefs.email_enabled}")
print(f"SMS enabled: {prefs.sms_enabled}")
print(f"Transaction notifications: {prefs.transaction_notifications}")
```

### Update Preferences

```python
# Enable SMS notifications
await notification_service.update_user_preferences(
    user_id="user123",
    preferences_update={
        "sms_enabled": True,
        "phone_number": "+1234567890",
    }
)

# Disable marketing notifications
await notification_service.update_user_preferences(
    user_id="user123",
    preferences_update={
        "marketing_notifications": False,
    }
)
```

### Notification Frequency

```python
from apps.shared.integration.wallet import NotificationFrequency

# Set to daily digest
await notification_service.update_user_preferences(
    user_id="user123",
    preferences_update={
        "notification_frequency": NotificationFrequency.DAILY_DIGEST,
        "digest_time": "09:00",  # Deliver at 9 AM
    }
)
```

## Notification History

### Get User's Notifications

```python
# Get last 50 notifications
notifications = await notification_service.get_user_notifications(
    user_id="user123",
    limit=50,
    offset=0
)

for notification in notifications:
    print(f"{notification.type}: {notification.subject}")
    print(f"Status: {notification.status}")
    print(f"Sent: {notification.sent_at}")
```

### Mark as Read

```python
await notification_service.mark_notification_read(
    notification_id="notif_123"
)
```

## API Endpoints

### Get Notification Preferences

```http
GET /api/wallet/notification-preferences
Authorization: Bearer <token>
```

Response:
```json
{
  "user_id": "user123",
  "email_enabled": true,
  "sms_enabled": true,
  "transaction_notifications": true,
  "security_notifications": true,
  "balance_notifications": true,
  "email": "user@example.com",
  "phone_number": "+1234567890"
}
```

### Update Notification Preferences

```http
PATCH /api/wallet/notification-preferences
Authorization: Bearer <token>
Content-Type: application/json

{
  "email_enabled": true,
  "sms_enabled": false,
  "transaction_notifications": true
}
```

### Get Notification History

```http
GET /api/wallet/notifications?limit=50&offset=0
Authorization: Bearer <token>
```

Response:
```json
[
  {
    "id": "notif_123",
    "type": "transaction_completed",
    "subject": "Transaction Completed - 100.00 USD",
    "message": "Your deposit transaction...",
    "status": "sent",
    "sent_at": "2025-10-27T10:30:00Z",
    "read_at": null
  }
]
```

## Environment Variables

```bash
# Email (Resend)
RESEND_API_KEY=re_xxxxx

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxxxx
TWILIO_AUTH_TOKEN=xxxxx
TWILIO_FROM_PHONE=+1234567890

# Sender information
NOTIFICATIONS_FROM_EMAIL=notifications@yourdomain.com
```

## Best Practices

### 1. Always Configure Preferences First

```python
# Set up user preferences when they sign up
await notification_service.update_user_preferences(
    user_id=new_user_id,
    preferences_update={
        "email": user.email,
        "email_enabled": True,
        "transaction_notifications": True,
        "security_notifications": True,
    }
)
```

### 2. Use Appropriate Priority

```python
# Regular transactions = NORMAL
await notification_service.send_notification(
    priority=NotificationPriority.NORMAL,
    ...
)

# Security issues = URGENT (sends via email AND SMS)
await notification_service.notify_suspicious_activity(
    priority=NotificationPriority.URGENT,
    ...
)
```

### 3. Handle Errors Gracefully

```python
try:
    await notification_service.notify_transaction_completed(transaction, wallet)
except Exception as e:
    logger.error(f"Notification failed: {e}")
    # Don't fail the transaction if notification fails
```

### 4. Test with Sandbox

```python
# Use test API keys for development
notification_service = NotificationService(
    database=db,
    resend_api_key="re_test_xxxxx",  # Resend test key
    twilio_config={
        "account_sid": "AC_test_xxxxx",  # Twilio test credentials
        "auth_token": "test_token",
    },
)
```

## Troubleshooting

### Notifications Not Sending

1. **Check user preferences**:
   ```python
   prefs = await notification_service.get_user_preferences(user_id)
   print(f"Email enabled: {prefs.email_enabled}")
   print(f"Email address: {prefs.email}")
   ```

2. **Check notification service is configured**:
   ```python
   if wallet_service.notification_service:
       print("✅ Notifications enabled")
   else:
       print("❌ Notifications NOT configured")
   ```

3. **Check logs**:
   ```bash
   # Look for notification errors
   grep "notification" /var/log/kasaai/*.log
   ```

### SMS Not Working

1. Verify Twilio credentials
2. Check phone number format (E.164: +1234567890)
3. Verify phone number is verified in Twilio sandbox

### Email Not Working

1. Verify Resend API key
2. Check sender email is verified domain
3. Check spam folder

## Examples

### Complete Integration Example

```python
from decimal import Decimal
from motor.motor_asyncio import AsyncIOMotorClient
from apps.shared.integration.wallet import (
    WalletService,
    NotificationService,
    PaymentProvider,
    Currency,
)
from apps.shared.integration.wallet.providers import StripeProvider

# Initialize
client = AsyncIOMotorClient("mongodb://localhost:27017")
db = client.kasaai_core

# Create notification service
notification_service = NotificationService(
    database=db,
    resend_api_key=os.getenv("RESEND_API_KEY"),
    twilio_config={
        "account_sid": os.getenv("TWILIO_ACCOUNT_SID"),
        "auth_token": os.getenv("TWILIO_AUTH_TOKEN"),
    },
    from_email="notifications@yourdomain.com",
    from_phone=os.getenv("TWILIO_FROM_PHONE"),
)

# Create wallet service with notifications
wallet_service = WalletService(
    database=db,
    notification_service=notification_service
)

# Register payment providers
stripe_config = ProviderConfig(...)
wallet_service.register_provider(
    PaymentProvider.STRIPE,
    StripeProvider(stripe_config)
)

# Setup user preferences
await notification_service.update_user_preferences(
    user_id="user123",
    preferences_update={
        "email": "user@example.com",
        "phone_number": "+1234567890",
        "email_enabled": True,
        "sms_enabled": True,
        "transaction_notifications": True,
        "security_notifications": True,
        "balance_notifications": True,
    }
)

# Create wallet
wallet = await wallet_service.get_or_create_wallet(
    user_id="user123",
    currency=Currency.USD,
    tenant_id="my_app"
)

# Process deposit (notification sent automatically)
transaction, payment_result = await wallet_service.deposit(
    wallet_id=wallet.id,
    amount=Decimal("100.00"),
    payment_provider=PaymentProvider.STRIPE,
    payment_method_id="pm_test_123"
)

# When webhook arrives, notification sent automatically
await wallet_service.process_deposit_success(
    transaction_id=transaction.id,
    provider_transaction_id="ch_123"
)
# ✅ User receives: "Transaction Completed - 100.00 USD"
```

## Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-core-backend -f`
- Email: support@kasaai.ailabsafrica.com
- Documentation: https://docs.kasaai.com/wallet/notifications
