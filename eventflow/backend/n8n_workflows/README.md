# EventFlow n8n Workflows

This directory contains n8n workflow templates for EventFlow notifications.

## Workflows

### 1. Task Reminder Notification
**File:** `task_reminder_notification.json`
**Purpose:** Send regular task reminders to responsible persons
**Channels:** Email + SMS
**Trigger:** Webhook at `/eventflow/task-reminder`

**Payload Example:**
```json
{
  "task_id": "68fbb02ab5fa6a18f64f3ca0",
  "event_id": "68fbae0ba629471be1b347fd",
  "event_name": "Impact Conference 2025",
  "task_title": "Arrange professional audio-visual and livestream",
  "task_priority": "critical",
  "task_deadline": "2025-11-15T00:00:00",
  "responsible_person": {
    "id": "68fbb20f6a3dc817bd37745c",
    "name": "Ama Adjei",
    "role": "Media Director",
    "phone": "+233244001002",
    "email": "ama@actionchapel.net"
  },
  "message": "Reminder: This task is due soon. Please update the status.",
  "notification_type": "task_reminder",
  "timestamp": "2025-10-24T17:00:00"
}
```

### 2. Deadline Alert (Critical)
**File:** `deadline_alert_notification.json`
**Purpose:** Urgent alerts for tasks approaching deadline (24h before)
**Channels:** Email + SMS (urgent styling)
**Trigger:** Webhook at `/eventflow/deadline-alert`

**Payload Example:**
```json
{
  "task_id": "68fbb02ab5fa6a18f64f3ca0",
  "event_id": "68fbae0ba629471be1b347fd",
  "event_name": "Impact Conference 2025",
  "task_title": "Arrange professional audio-visual and livestream",
  "task_priority": "critical",
  "task_deadline": "2025-11-15T00:00:00",
  "hours_remaining": 24,
  "responsible_person": {
    "id": "68fbb20f6a3dc817bd37745c",
    "name": "Ama Adjei",
    "role": "Media Director",
    "phone": "+233244001002",
    "email": "ama@actionchapel.net"
  },
  "notification_type": "deadline_alert",
  "timestamp": "2025-10-24T17:00:00"
}
```

## Installation

### Prerequisites
1. n8n instance running at https://automations.ailabsafrica.com
2. n8n API key configured
3. Email credentials (Resend API or SMTP)
4. SMS credentials (Twilio)

### Import Workflows

1. **Via n8n Web UI:**
   ```
   1. Go to https://automations.ailabsafrica.com
   2. Click "+ Workflow" > "Import from File"
   3. Select the workflow JSON file
   4. Configure credentials (Resend, Twilio)
   5. Activate the workflow
   ```

2. **Via n8n CLI:**
   ```bash
   export N8N_API_KEY="your-api-key"
   export N8N_BASE_URL="https://automations.ailabsafrica.com"

   # Import workflow
   n8n import:workflow --input=task_reminder_notification.json

   # List workflows
   n8n list:workflow
   ```

3. **Via API:**
   ```python
   import requests

   n8n_base_url = "https://automations.ailabsafrica.com"
   n8n_api_key = "your-api-key"

   with open("task_reminder_notification.json") as f:
       workflow_data = json.load(f)

   response = requests.post(
       f"{n8n_base_url}/api/v1/workflows",
       headers={"X-N8N-API-KEY": n8n_api_key},
       json=workflow_data
   )
   ```

## Configuration

### Required Environment Variables (in n8n)

```bash
# Email (Resend)
RESEND_API_KEY=re_xxx

# SMS (Twilio)
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_AUTH_TOKEN=xxx
TWILIO_PHONE_NUMBER=+1234567890
```

### Credentials Setup

1. **Resend (Email)**
   - Go to Credentials > Add Credential
   - Select "HTTP Header Auth"
   - Name: "Resend API"
   - Header Name: "Authorization"
   - Header Value: "Bearer YOUR_RESEND_API_KEY"

2. **Twilio (SMS)**
   - Go to Credentials > Add Credential
   - Select "Basic Auth"
   - Name: "Twilio API"
   - Username: YOUR_TWILIO_ACCOUNT_SID
   - Password: YOUR_TWILIO_AUTH_TOKEN

## Testing

### Test Task Reminder
```bash
curl -X POST https://automations.ailabsafrica.com/webhook/eventflow/task-reminder \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test_task_123",
    "event_name": "Test Event",
    "task_title": "Test Task",
    "task_priority": "high",
    "task_deadline": "2025-12-01T00:00:00",
    "responsible_person": {
      "name": "Test Person",
      "phone": "+233244001001",
      "email": "test@example.com"
    },
    "message": "This is a test notification"
  }'
```

### Test Deadline Alert
```bash
curl -X POST https://automations.ailabsafrica.com/webhook/eventflow/deadline-alert \
  -H "Content-Type: application/json" \
  -d '{
    "task_id": "test_task_123",
    "event_name": "Test Event",
    "task_title": "Urgent Test Task",
    "task_priority": "critical",
    "task_deadline": "2025-12-01T00:00:00",
    "hours_remaining": 12,
    "responsible_person": {
      "name": "Test Person",
      "phone": "+233244001001",
      "email": "test@example.com"
    }
  }'
```

## EventFlow Backend Integration

The EventFlow backend can trigger these workflows via the n8n integration:

```python
from apps.shared.integration.n8n import N8NIntegration, N8NConfig

# Initialize n8n
n8n_config = N8NConfig(
    base_url="https://automations.ailabsafrica.com",
    api_key=os.getenv("N8N_API_KEY")
)
n8n = N8NIntegration(n8n_config)

# Trigger task reminder
notification_data = {
    "task_id": task_id,
    "event_name": event_name,
    "task_title": task_title,
    "task_priority": task_priority,
    "task_deadline": task_deadline.isoformat(),
    "responsible_person": {
        "name": person_name,
        "phone": person_phone,
        "email": person_email
    },
    "message": "Reminder: Please update task status"
}

# Trigger via webhook
import requests
response = requests.post(
    f"{n8n_config.base_url}/webhook/eventflow/task-reminder",
    json=notification_data
)
```

## Troubleshooting

### Workflow not triggering
1. Check workflow is activated (green toggle)
2. Verify webhook URL is correct
3. Check n8n logs for errors
4. Test webhook URL with curl

### Notifications not sending
1. Verify credentials are configured
2. Check email/SMS provider API keys
3. Review n8n execution logs
4. Test credentials manually

### Email formatting issues
1. Check HTML template syntax in workflow
2. Test with different email clients
3. Verify data extraction from webhook payload

## Additional Workflows to Create

- **Task Escalation Alert** - Notify organizer when task is blocked
- **Daily Summary Report** - Send daily digest of all tasks status
- **Event Status Update** - Notify team when event status changes
- **Team Progress Report** - Weekly summary for event organizer

## Support

For issues or questions:
- Check n8n logs: https://automations.ailabsafrica.com/executions
- Review EventFlow backend logs: `sudo journalctl -u eventflow -f`
- Contact: support@ailabsafrica.com
