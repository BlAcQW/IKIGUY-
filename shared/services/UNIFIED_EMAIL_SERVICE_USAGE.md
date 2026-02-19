# Unified Email Service - Usage Guide

## Overview
The Unified Email Service provides a centralized, easy-to-use interface for sending emails across all KasaAI applications. It automatically configures itself from environment variables and provides fallback mechanisms for reliable delivery.

## Features
- ✅ Automatic configuration from environment variables
- ✅ SMTP support with TLS (iRedMail)
- ✅ Automatic fallback to Resend/SendGrid if SMTP fails
- ✅ HTML and plain text email support
- ✅ Attachments support
- ✅ CC/BCC support
- ✅ Custom reply-to addresses
- ✅ Comprehensive logging
- ✅ Singleton pattern for efficient resource usage

## Installation
The service is located in `@shared/services/` and is automatically available to all apps in the monorepo.

```python
from shared.services.unified_email_service import get_email_service, send_email
```

## Environment Variables
Configure the following in your `.env` file:

```bash
# Primary SMTP Configuration (iRedMail)
SMTP_HOST=mail.ailabsafrica.com
SMTP_PORT=587
SMTP_USERNAME=noreply@ailabsafrica.com
SMTP_PASSWORD=your_password_here
SMTP_USE_TLS=true
SMTP_TIMEOUT=30

# Default Sender Information
SENDER_EMAIL=noreply@ailabsafrica.com
SENDER_NAME=KasaAI Platform

# Fallback Services (Optional)
RESEND_API=your_resend_api_key_here
SENDGRID_API_KEY=your_sendgrid_api_key_here

# Other Settings
DEFAULT_EMAIL_RECIPIENT=ailabsafrica@gmail.com
EMAIL_ENABLE_FALLBACK=true
```

## Basic Usage

### Method 1: Using the Service Instance
```python
from shared.services.unified_email_service import get_email_service

# Get the email service
email_service = get_email_service()

# Send a simple email
result = await email_service.send_email(
    to="user@example.com",
    subject="Welcome to KasaAI",
    body="Thank you for joining us!",
    html_body="<h1>Welcome to KasaAI</h1><p>Thank you for joining us!</p>"
)

if result["success"]:
    print(f"✅ Email sent! Message ID: {result['message_id']}")
else:
    print(f"❌ Email failed: {result['error']}")
```

### Method 2: Using the Convenience Function
```python
from shared.services.unified_email_service import send_email

# Send email directly
result = await send_email(
    to="user@example.com",
    subject="Welcome to KasaAI",
    body="Thank you for joining us!"
)
```

## Advanced Usage

### Sending HTML Emails
```python
html_content = """
<html>
<body>
    <h1>Welcome to KasaAI!</h1>
    <p>We're excited to have you on board.</p>
    <p><a href="https://kasaai.ailabsafrica.com">Get Started</a></p>
</body>
</html>
"""

result = await email_service.send_email(
    to="user@example.com",
    subject="Welcome to KasaAI",
    body="Welcome to KasaAI! We're excited to have you.",
    html_body=html_content
)
```

### Sending with CC and BCC
```python
result = await email_service.send_email(
    to="primary@example.com",
    subject="Team Update",
    body="Here's the latest update...",
    cc=["manager@example.com", "team-lead@example.com"],
    bcc=["archive@example.com"]
)
```

### Sending with Attachments
```python
# Prepare attachment
attachment_data = {
    "filename": "report.pdf",
    "content": pdf_bytes,  # Binary content
    "content_type": "application/pdf"
}

result = await email_service.send_email(
    to="client@example.com",
    subject="Monthly Report",
    body="Please find attached your monthly report.",
    attachments=[attachment_data]
)
```

### Custom Sender and Reply-To
```python
result = await email_service.send_email(
    to="customer@example.com",
    subject="Support Response",
    body="Thank you for contacting us...",
    from_email="support@ailabsafrica.com",
    from_name="KasaAI Support Team",
    reply_to="replies@ailabsafrica.com"
)
```

### Template Emails (Basic)
```python
template_vars = {
    "subject": "Order Confirmation",
    "body": "Your order #12345 has been confirmed.",
    "html_body": "<h1>Order Confirmed</h1><p>Order #12345</p>"
}

result = await email_service.send_template_email(
    to="customer@example.com",
    template_name="order_confirmation",
    template_variables=template_vars
)
```

## Integration Examples

### FastAPI Integration
```python
from fastapi import APIRouter, BackgroundTasks
from shared.services.unified_email_service import send_email

router = APIRouter()

@router.post("/send-notification")
async def send_notification(background_tasks: BackgroundTasks):
    """Send email notification in background."""

    background_tasks.add_task(
        send_email,
        to="admin@ailabsafrica.com",
        subject="New User Signup",
        body="A new user has signed up!"
    )

    return {"status": "Email queued"}
```

### VAPI Integration Webhook
```python
from shared.services.unified_email_service import get_email_service

async def handle_email_send(args: Dict[str, Any], background_tasks: BackgroundTasks):
    """Handle email sending from VAPI assistant."""
    email_service = get_email_service()

    to_email = args.get("to_email", "ailabsafrica@gmail.com")
    subject = args.get("subject", "Voice Assistant Notification")
    message = args.get("message", "")

    html_content = f"""
    <html>
    <body>
        <h2>{subject}</h2>
        <p>{message}</p>
        <p><strong>Sent at:</strong> {datetime.now().isoformat()}</p>
    </body>
    </html>
    """

    result = await email_service.send_email(
        to=to_email,
        subject=subject,
        body=message,
        html_body=html_content
    )

    return result
```

### Call Management Integration
```python
from shared.services.unified_email_service import send_email

async def send_call_summary(call_id: str, summary: str):
    """Send call summary email."""

    result = await send_email(
        to="ailabsafrica@gmail.com",
        subject=f"Call Summary - {call_id}",
        body=summary,
        html_body=f"<h2>Call Summary</h2><p>{summary}</p>"
    )

    if result["success"]:
        logger.info(f"✅ Call summary email sent for {call_id}")
    else:
        logger.error(f"❌ Failed to send call summary: {result['error']}")
```

## Response Format
All methods return a dictionary with the following structure:

### Success Response
```python
{
    "success": True,
    "message_id": "<unique-message-id>",
    "provider": "smtp",  # or "resend", "sendgrid"
    "smtp_host": "mail.ailabsafrica.com",
    "smtp_port": 587,
    "recipients": ["user@example.com"],
    "from_address": "noreply@ailabsafrica.com",
    "subject": "Email Subject",
    "sent_at": "2025-11-05T10:00:00"
}
```

### Error Response
```python
{
    "success": False,
    "error": "Connection timeout",
    "provider": "smtp"
}
```

## Error Handling
The service automatically handles errors and provides fallback mechanisms:

```python
result = await send_email(
    to="user@example.com",
    subject="Test",
    body="Hello"
)

if not result["success"]:
    error_message = result["error"]
    provider = result["provider"]

    # Log error
    logger.error(f"Email failed via {provider}: {error_message}")

    # Handle specific errors
    if "timeout" in error_message.lower():
        # Handle timeout
        pass
    elif "authentication" in error_message.lower():
        # Handle auth error
        pass
```

## Fallback Mechanism
The service automatically tries multiple providers:

1. **Primary**: SMTP (iRedMail) via mail.ailabsafrica.com
2. **Fallback 1**: Resend API (if configured)
3. **Fallback 2**: SendGrid API (if configured)

Example flow:
```
SMTP Attempt → Success ✅
    ↓ (If fails)
Resend API Attempt → Success ✅
    ↓ (If fails)
SendGrid API Attempt → Success/Fail
```

## Testing

### Unit Testing
```python
import pytest
from shared.services.unified_email_service import UnifiedEmailService, reset_email_service

@pytest.mark.asyncio
async def test_send_email():
    # Reset service for clean test
    reset_email_service()

    # Configure test service
    test_config = {
        "smtp_enabled": True,
        "smtp_host": "localhost",
        "smtp_port": 25,
        "from_email": "test@example.com"
    }

    service = UnifiedEmailService(config=test_config)

    result = await service.send_email(
        to="recipient@example.com",
        subject="Test",
        body="Test email"
    )

    assert result["success"] == True
```

### Integration Testing
```python
from shared.services.unified_email_service import send_email

async def test_integration():
    """Test email sending in development environment."""
    result = await send_email(
        to="dev@ailabsafrica.com",
        subject="Integration Test",
        body="This is a test email from integration tests."
    )

    print(f"Test result: {result}")
    assert result["success"] == True
```

## Best Practices

### 1. Use Background Tasks for Non-Critical Emails
```python
from fastapi import BackgroundTasks

background_tasks.add_task(
    send_email,
    to="user@example.com",
    subject="Welcome",
    body="Welcome message"
)
```

### 2. Handle Errors Gracefully
```python
result = await send_email(to="...", subject="...", body="...")
if not result["success"]:
    # Log error but don't fail the entire operation
    logger.error(f"Email failed: {result['error']}")
```

### 3. Use HTML for Rich Content
```python
# Create rich, professional-looking emails
html = """
<html>
<body style="font-family: Arial, sans-serif;">
    <h1 style="color: #2563eb;">Welcome!</h1>
    <p>We're excited to have you.</p>
</body>
</html>
"""
```

### 4. Validate Email Addresses
```python
import re

def is_valid_email(email: str) -> bool:
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

if is_valid_email(recipient):
    await send_email(to=recipient, ...)
```

## Monitoring and Logging
The service provides comprehensive logging:

```python
# Logs are automatically generated:
# ✅ Email sent successfully via SMTP to user@example.com
# 📤 Connecting to SMTP server: mail.ailabsafrica.com:587
# 🔐 Starting TLS encryption...
# 🔑 Authenticating as: noreply@ailabsafrica.com
# ✅ SMTP email sent successfully - Message ID: <unique-id>
```

## Troubleshooting

### Common Issues

**1. SMTP Connection Timeout**
```python
# Increase timeout in environment variables
SMTP_TIMEOUT=60
```

**2. Authentication Failed**
```python
# Verify credentials
SMTP_USERNAME=noreply@ailabsafrica.com
SMTP_PASSWORD=correct_password
```

**3. TLS Errors**
```python
# Try disabling TLS for local testing
SMTP_USE_TLS=false
```

**4. Port Blocked**
```python
# Try alternative port
SMTP_PORT=25  # or 465 for SSL
```

## Migration from Old Code

### Before (Old Code)
```python
import smtplib
from email.mime.text import MIMEText

smtp_server = "localhost"
msg = MIMEText("Hello")
msg['Subject'] = "Test"
msg['From'] = "sender@example.com"
msg['To'] = "recipient@example.com"

server = smtplib.SMTP(smtp_server, 25)
server.sendmail(sender, recipient, msg.as_string())
server.quit()
```

### After (Unified Service)
```python
from shared.services.unified_email_service import send_email

result = await send_email(
    to="recipient@example.com",
    subject="Test",
    body="Hello"
)
```

## Support
For issues or questions:
- Check logs for detailed error messages
- Verify environment variables are set correctly
- Test SMTP connectivity: `telnet mail.ailabsafrica.com 587`
- Review the source code: `@shared/services/unified_email_service.py`
