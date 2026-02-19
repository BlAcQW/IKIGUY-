# SMS Campaign System - Integration Guide for All Apps

## Overview

The SMS Campaign system is now fully centralized in `@shared/` and ready for integration across all AI Labs Africa applications (B2C Portal, StudyFlow, InkWave, EventFlow, etc.).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Your App Frontend                       │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Import Shared Component:                            │  │
│  │  import { SMSCampaignAnalytics }                     │  │
│  │    from '@shared/frontend/sms-campaigns'             │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ HTTP Requests
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                    Your App Backend                         │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  from shared.services.sms_campaign_service           │  │
│  │    import sms_campaign_service                       │  │
│  │                                                        │  │
│  │  Routes: /sms-campaigns/*                            │  │
│  │  - POST /         (create)                           │  │
│  │  - GET /          (list)                             │  │
│  │  - GET /{id}      (get one)                          │  │
│  │  - PUT /{id}      (update)                           │  │
│  │  - POST /{id}/prepare (prepare messages)            │  │
│  │  - POST /{id}/start   (start sending)               │  │
│  │  - POST /{id}/pause   (pause)                       │  │
│  │  - GET /{id}/messages (analytics)                   │  │
│  │  - GET /{id}/status-stream (real-time SSE)         │  │
│  └──────────────────────────────────────────────────────┘  │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            @shared/services/sms_campaign_service.py         │
│  - Campaign CRUD                                            │
│  - Message tracking                                         │
│  - Auto-execution with rate limiting                        │
│  - Provider integration (Arkesel, Twilio)                   │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start (3 Steps)

### Step 1: Backend - Add SMS Campaign Routes

Copy the reference implementation from `core_backend/routes/sms_campaigns.py` to your app's routes:

```python
# In your_app/backend/app/api/routes/ or backend/routes/
# Create: sms_campaigns.py

from fastapi import APIRouter, HTTPException, Depends, Request
from shared.services.sms_campaign_service import sms_campaign_service, SMSCampaignService
from shared.integration.sms import SMSIntegration

router = APIRouter(prefix="/sms-campaigns", tags=["sms-campaigns"])

# Initialize SMS service (do this once in main.py or as needed)
def get_sms_service():
    sms_config = {
        "providers": {
            "arkesel": {
                "api_key": os.getenv("ARKESEL_API_KEY"),
                "sender_id": os.getenv("ARKESEL_SENDER_ID")
            }
        },
        "default_provider": "arkesel"
    }
    sms_integration = SMSIntegration(sms_config)
    sms_campaign_service.set_sms_provider(sms_integration)
    sms_campaign_service.set_database(get_database())
    return sms_campaign_service

# Then add all the endpoints from core_backend/routes/sms_campaigns.py
# They're already implemented and tested!
```

**Key Endpoints to Include:**
1. `POST /` - Create campaign
2. `GET /` - List campaigns
3. `GET /{id}` - Get campaign
4. `PUT /{id}` - Update campaign
5. `POST /{id}/prepare` - Prepare messages from audience
6. `POST /{id}/start` - Start campaign
7. `POST /{id}/pause` - Pause campaign
8. `GET /{id}/messages` - Get message list with filters ⭐
9. `GET /{id}/status-stream` - Real-time SSE updates ⭐
10. `GET /{id}/analytics` - Get analytics

### Step 2: Backend - Add Auto-Resume in main.py

```python
# In your_app/backend/main.py or app/main.py

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan."""
    # Startup
    logger.info("Starting app...")
    await connect_to_mongodb()

    # Resume running SMS campaigns after server restart
    try:
        from shared.services.sms_campaign_service import sms_campaign_service, SMSCampaignStatus
        from shared.integration.sms import SMSIntegration

        # Initialize SMS service
        sms_config = {
            "providers": {
                "arkesel": {
                    "api_key": os.getenv("ARKESEL_API_KEY"),
                    "sender_id": os.getenv("ARKESEL_SENDER_ID")
                }
            },
            "default_provider": "arkesel"
        }
        sms_integration = SMSIntegration(sms_config)
        sms_campaign_service.set_sms_provider(sms_integration)
        sms_campaign_service.set_database(get_database())

        # Resume running campaigns
        all_campaigns = await sms_campaign_service.list_campaigns(
            organization_id="",  # Get all
            status=None,
            limit=1000
        )

        resumed = 0
        for campaign in all_campaigns:
            if campaign.status == SMSCampaignStatus.RUNNING:
                await sms_campaign_service.start_campaign(campaign.id, force_resume=True)
                resumed += 1

        logger.info(f"✅ Resumed {resumed} running SMS campaigns")

    except Exception as e:
        logger.error(f"❌ Failed to resume campaigns: {e}")

    yield

    # Shutdown
    logger.info("Shutting down...")
    await close_mongodb_connection()
```

### Step 3: Frontend - Use Shared Component

```tsx
// In your_app/frontend/src/pages/SMSCampaigns.tsx

import React, { useState, useEffect } from 'react';
import { SMSCampaignAnalytics } from '../../../shared/frontend/sms-campaigns/SMSCampaignAnalytics';
import { API_BASE_URL } from '@/config/api-config';

export const SMSCampaignsPage = () => {
  const [campaigns, setCampaigns] = useState([]);
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const token = localStorage.getItem('access_token');

  // Fetch campaigns
  useEffect(() => {
    fetch(`${API_BASE_URL}/sms-campaigns/`, {
      headers: { 'Authorization': `Bearer ${token}` }
    })
      .then(res => res.json())
      .then(data => setCampaigns(data.campaigns));
  }, []);

  // Handle campaign actions
  const handleAction = async (action, campaignId) => {
    const endpoints = {
      'start': `/sms-campaigns/${campaignId}/start`,
      'pause': `/sms-campaigns/${campaignId}/pause`,
      'edit': `/sms-campaigns/${campaignId}`,  // Use PUT
      'duplicate': `/sms-campaigns/${campaignId}/duplicate`
    };

    await fetch(`${API_BASE_URL}${endpoints[action]}`, {
      method: action === 'edit' ? 'PUT' : 'POST',
      headers: { 'Authorization': `Bearer ${token}` }
    });

    // Refresh list
    // ...
  };

  return (
    <div>
      {/* Your campaign list UI */}
      <table>
        {campaigns.map(campaign => (
          <tr key={campaign.id} onClick={() => {
            setSelectedCampaign(campaign);
            setShowAnalytics(true);
          }}>
            <td>{campaign.name}</td>
            <td>{campaign.status}</td>
            <td>{campaign.progress.sent}/{campaign.progress.total_recipients}</td>
          </tr>
        ))}
      </table>

      {/* Shared Analytics Modal */}
      <SMSCampaignAnalytics
        campaign={selectedCampaign}
        isOpen={showAnalytics}
        onClose={() => setShowAnalytics(false)}
        apiBaseUrl={API_BASE_URL}
        authToken={token}
        onAction={handleAction}
      />
    </div>
  );
};
```

## Features You Get

### ✅ Backend (Centralized in @shared/)

1. **SMS Campaign Service** (`@shared/services/sms_campaign_service.py`)
   - Campaign CRUD operations
   - Message preparation from audiences
   - Auto-execution with rate limiting (1 msg/sec configurable)
   - Provider integration (Arkesel, Twilio)
   - Status tracking (draft, running, paused, completed, failed)

2. **Auto-Resume on Restart**
   - Campaigns automatically continue after server restarts
   - Only "running" campaigns resume (paused stay paused)
   - No duplicate messages sent

3. **Message Tracking**
   - Individual message status (sent, failed, pending, delivered)
   - Error messages for failed sends
   - Cost tracking per message
   - Timestamps for all state changes

### ✅ Frontend (Shared Component)

1. **SMSCampaignAnalytics Component** (`@shared/frontend/sms-campaigns/`)
   - 4 tabs: Overview, Successful, Failed, All Messages
   - Real-time progress bar
   - Message-level details with error reporting
   - Recipient information (name, phone, email)
   - Action buttons (Start, Pause, Edit, Duplicate)

2. **Real-Time Updates** (via SSE)
   - Live progress updates every 2 seconds
   - Auto-closes when campaign completes
   - No polling required

## App-Specific Considerations

### Audiences

Each app defines "audiences" differently:

- **B2C Portal**: Uses `audience_id` from audiences table (generic contacts)
- **ChurchFlow**: Uses conference/branch/session filters to build audience
- **StudyFlow**: Could use course/cohort/student filters
- **InkWave**: Could use subscriber lists

**Solution**: The shared service accepts a generic `audience_id`. Your app's backend should:
1. Create an audience record (contacts list)
2. Pass the `audience_id` when creating a campaign
3. Use `/sms-campaigns/{id}/prepare` to generate messages from audience

Example for StudyFlow:
```python
# Create audience from course students
audience = {
    "id": "course-123-students",
    "name": "Computer Science 101 Students",
    "contacts": [
        {"phone": "+233...", "name": "Student 1", "email": "..."},
        {"phone": "+233...", "name": "Student 2", "email": "..."}
    ]
}

# Create campaign
campaign = await sms_campaign_service.create_campaign(
    name="Assignment Due Reminder",
    template_content="Hi {{name}}, your {{assignment}} is due {{date}}!",
    audience_id=audience["id"],
    organization_id=org_id,
    user_id=user_id
)

# Prepare messages
await sms_campaign_service.prepare_campaign_messages(
    campaign_id=campaign.id,
    contacts=audience["contacts"]
)

# Start campaign
await sms_campaign_service.start_campaign(campaign.id)
```

## Database Schema

The shared service uses these MongoDB collections:

### `sms_campaigns`
```json
{
  "id": "uuid",
  "name": "Campaign Name",
  "organization_id": "org-123",
  "user_id": "user-456",
  "template_content": "Hi {{name}}, ...",
  "audience_id": "audience-789",
  "status": "running",
  "progress": {
    "total_recipients": 5000,
    "sent": 3000,
    "delivered": 2900,
    "failed": 100,
    "pending": 2000
  },
  "config": {
    "send_rate_per_second": 1.0,
    "batch_size": 100,
    "retry_failed": true,
    "max_retries": 2,
    "sender_id": "COMPANY"
  },
  "total_cost": 150.00,
  "sms_provider": "arkesel",
  "created_at": "2025-12-02T...",
  "started_at": "2025-12-02T...",
  "completed_at": null
}
```

### `sms_campaign_messages`
```json
{
  "id": "uuid",
  "campaign_id": "campaign-123",
  "recipient_phone": "+233501234567",
  "recipient_name": "John Doe",
  "recipient_email": "john@example.com",
  "recipient_data": {...},
  "message_content": "Hi John, ...",
  "status": "sent",
  "sent_at": "2025-12-02T...",
  "delivered_at": null,
  "failed_at": null,
  "error_message": null,
  "provider_message_id": "twilio-msg-123",
  "cost": 0.05,
  "retry_count": 0
}
```

## Environment Variables

Add to your `.env`:

```bash
# SMS Provider (Arkesel)
ARKESEL_API_KEY=your-api-key
ARKESEL_SENDER_ID=YOURCOMPANY

# SMS Provider (Twilio) - Optional
TWILIO_ACCOUNT_SID=your-account-sid
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_PHONE_NUMBER=+1234567890
```

## Testing

### 1. Test Backend Endpoints

```bash
# Create campaign
curl -X POST http://localhost:8000/sms-campaigns/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Campaign",
    "template_content": "Hi {{name}}, this is a test!",
    "audience_id": "test-audience"
  }'

# Start campaign
curl -X POST http://localhost:8000/sms-campaigns/{id}/start \
  -H "Authorization: Bearer $TOKEN"

# Get messages
curl http://localhost:8000/sms-campaigns/{id}/messages?status=failed \
  -H "Authorization: Bearer $TOKEN"
```

### 2. Test Frontend Component

1. Open your app's SMS Campaigns page
2. Click on a campaign row
3. Verify modal opens with 4 tabs
4. Switch to "Failed" tab - should see error messages
5. Switch to "Successful" tab - should see sent messages
6. Check Overview tab for progress bar

### 3. Test Auto-Resume

1. Create and start a campaign
2. Restart your backend server
3. Check logs for "✅ Resumed X running SMS campaigns"
4. Verify campaign continues sending

## Apps Integration Status

| App | Status | Notes |
|-----|--------|-------|
| **ChurchFlow** | ✅ Deployed | Advanced implementation with conference filters |
| **B2C Portal** | 🚧 In Progress | Using generic audience_id, ready for upgrade |
| **Core Backend** | ✅ Enhanced | All endpoints added, auto-resume enabled |
| **StudyFlow** | 📋 Planned | Course/student notifications |
| **InkWave** | 📋 Planned | Audiobook updates |
| **EventFlow** | 📋 Planned | Event reminders |

## Support & Troubleshooting

### Common Issues

**1. Messages not sending after restart**
- Check logs for "✅ Resumed X running campaigns"
- Verify SMS provider credentials in `.env`
- Check MongoDB connection

**2. Frontend component not rendering**
- Ensure Tailwind CSS is configured
- Install `lucide-react`: `npm install lucide-react`
- Check import path from `@shared/frontend/sms-campaigns`

**3. Failed messages with "No valid number"**
- Check phone number format (Ghana: +233XXXXXXXXX or 0XXXXXXXXX)
- Use phone validation at registration/import
- Filter international numbers for Ghana-only providers

### Debug Mode

Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("shared.services.sms_campaign_service")
logger.setLevel(logging.DEBUG)
```

## Next Steps

1. **For New Apps**: Follow the Quick Start (3 steps above)
2. **For Existing Apps**: Replace your current SMS campaign implementation with the shared version
3. **Test**: Run through the testing checklist
4. **Deploy**: Restart your backend to enable auto-resume

## Reference Implementations

- **Full Backend**: `apps/core_backend/backend/routes/sms_campaigns.py`
- **Frontend Component**: `apps/shared/frontend/sms-campaigns/SMSCampaignAnalytics.tsx`
- **Service Logic**: `apps/shared/services/sms_campaign_service.py`
- **Live Example**: ChurchFlow SMS Campaigns (https://churchflow.ailabsafrica.com)

---

**Last Updated**: December 2, 2025
**Version**: 1.0
**Maintained By**: AI Labs Africa Platform Team
