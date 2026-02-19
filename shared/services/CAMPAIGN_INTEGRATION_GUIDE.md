# Centralized Campaign System Integration Guide

## Overview

The centralized campaign system provides **complete, plug-and-play marketing campaign functionality** for all applications in the KasaAI ecosystem. With this integration, your app instantly gets:

- **Multi-channel campaigns**: Voice (Vapi), SMS (Arkesel), WhatsApp, Email
- **Contact/lead management**: Full CRUD, import/export, segmentation
- **Campaign analytics**: Delivery rates, open rates, cost tracking
- **Unified API**: Single router with all campaign endpoints

## 🎯 What You Get

### Features Included:

1. **Campaign Management**
   - Create, read, update, delete campaigns
   - Launch and pause campaigns
   - Real-time progress tracking
   - Cost analytics

2. **Contact Management**
   - Contact CRUD operations
   - CSV import/export
   - Segmentation & filtering
   - Opt-out management
   - Contact statistics

3. **Multi-Channel Delivery**
   - **Voice**: Automated voice calls via Vapi
   - **SMS**: Text messages via Arkesel
   - **WhatsApp**: WhatsApp Business API
   - **Email**: SMTP/Resend integration

4. **Segmentation**
   - Filter by tags, contact type, interest level
   - Date range filtering
   - Custom app-specific filters
   - Preview segment before launch

5. **Analytics**
   - Delivery rates
   - Open/click rates
   - Failure rates
   - Cost per delivery
   - Campaign duration

## 📦 Installation (3 Steps)

### Step 1: Import the Router

In your app's main API file (e.g., `backend/app/api/__init__.py`):

```python
from shared.routers.campaign_router import get_campaign_router
from app.core.database import get_database
from app.core.auth import get_current_user, get_organization_context

# Create campaign router
campaign_router = get_campaign_router(
    get_database_func=get_database,
    get_current_user_func=get_current_user,
    get_org_context_func=get_organization_context
)

# Include in your app
app.include_router(campaign_router, prefix="/api/v1")
```

### Step 2: Done!

That's it. Your app now has complete campaign functionality at:
- `POST /api/v1/campaigns` - Create campaign
- `GET /api/v1/campaigns` - List campaigns
- `POST /api/v1/campaigns/{id}/launch` - Launch campaign
- `GET /api/v1/campaigns/{id}/analytics` - Get analytics
- `POST /api/v1/campaigns/contacts` - Create contact
- `GET /api/v1/campaigns/contacts` - List contacts
- `POST /api/v1/campaigns/contacts/import` - Import CSV
- ... and 10+ more endpoints

### Step 3 (Optional): Add Frontend Components

See "Frontend Integration" section below for React components.

## 🔧 Using the Services Directly

If you want to use the services in your backend code (not via API):

### Campaign Service

```python
from shared.services.unified_campaign_service import UnifiedCampaignService
from shared.models.campaign import CampaignCreate, CampaignType, MessageTemplate

# Initialize
campaign_service = UnifiedCampaignService(database=db)

# Create campaign
campaign_data = CampaignCreate(
    name="Property Viewing Invites",
    campaign_type=CampaignType.SMS,
    message_template=MessageTemplate(
        text_content="Hi {{name}}, we have a new property at {{location}} that matches your preferences!"
    ),
    segment_filter=SegmentFilter(
        tags=["interested", "budget-500k"]
    )
)

campaign = await campaign_service.create_campaign(
    campaign_data=campaign_data,
    organization_id=org_id,
    user_id=user_id
)

# Launch campaign
await campaign_service.launch_campaign(campaign.id, org_id)

# Get analytics
analytics = await campaign_service.get_campaign_analytics(campaign.id, org_id)
print(f"Sent: {analytics.sent}, Delivered: {analytics.delivered}")
```

### Contact Service

```python
from shared.services.contact_service import ContactService
from shared.models.contact import ContactCreate, ContactType, InterestLevel

# Initialize
contact_service = ContactService(database=db)

# Create contact
contact_data = ContactCreate(
    first_name="John",
    last_name="Doe",
    email="john@example.com",
    phone="+233241234567",
    contact_type=ContactType.LEAD,
    interest_level=InterestLevel.HOT,
    tags=["property-seeker", "budget-500k"],
    custom_data={
        "property_type": "apartment",
        "location_preference": "Accra",
        "budget": 500000
    }
)

contact = await contact_service.create_contact(
    contact_data=contact_data,
    organization_id=org_id
)

# Import from CSV
csv_content = """first_name,last_name,email,phone,tags
Jane,Smith,jane@example.com,+233241234568,interested
Bob,Johnson,bob@example.com,+233241234569,high-value"""

result = await contact_service.import_contacts(
    organization_id=org_id,
    csv_content=csv_content
)
print(f"Imported {result.imported} contacts")
```

## 📝 Campaign Models

### Campaign Structure

```python
{
    "id": "campaign_123",
    "organization_id": "org_456",
    "user_id": "user_789",
    "name": "New Property Alerts",
    "campaign_type": "sms",  # or "email", "whatsapp", "voice"
    "status": "running",     # draft, scheduled, running, paused, completed

    "message_template": {
        "text_content": "Hi {{name}}, check out our new listing at {{address}}!",
        "subject": None,        # For email
        "html_content": None,   # For email
        "voice_id": None        # For voice (Vapi assistant ID)
    },

    "segment_filter": {
        "tags": ["interested"],
        "created_after": "2025-01-01",
        "exclude_opted_out": True
    },

    "target_count": 150,
    "sent_count": 120,
    "delivered_count": 115,
    "failed_count": 5,
    "total_cost": 6.00,
    "currency": "GHS",

    "schedule_config": {
        "scheduled_start": None,
        "business_hours_only": True,
        "exclude_weekends": True
    },

    "delivery_config": {
        "max_concurrent": 10,
        "rate_per_second": 1.0,
        "max_retries": 2
    }
}
```

### Contact Structure

```python
{
    "id": "contact_123",
    "organization_id": "org_456",

    "first_name": "John",
    "last_name": "Doe",
    "email": "john@example.com",
    "phone": "+233241234567",
    "whatsapp_number": "+233241234567",

    "contact_type": "lead",          # lead, customer, prospect
    "interest_level": "hot",         # hot, warm, cold
    "tags": ["property-seeker"],
    "segments": ["high-value"],
    "source": "website",

    "opt_out_channels": [],          # ["email", "sms", "whatsapp", "voice"]

    "custom_data": {
        # App-specific fields
        "property_type": "apartment",
        "budget": 500000
    },

    "total_campaigns_sent": 5,
    "total_campaigns_opened": 3,
    "last_contacted": "2025-12-08T10:00:00Z"
}
```

## 🎨 Frontend Integration

### React/TypeScript Integration

Create `src/lib/api/campaign-api.ts`:

```typescript
import { API_BASE_URL } from './config';

export interface Campaign {
  id: string;
  name: string;
  campaign_type: 'sms' | 'email' | 'whatsapp' | 'voice';
  status: 'draft' | 'scheduled' | 'running' | 'completed';
  sent_count: number;
  delivered_count: number;
  total_cost: number;
}

export const campaignApi = {
  // List campaigns
  async listCampaigns() {
    const response = await fetch(`${API_BASE_URL}/api/v1/campaigns`, {
      headers: {
        'Authorization': `Bearer ${getToken()}`
      }
    });
    return response.json();
  },

  // Create campaign
  async createCampaign(data: any) {
    const response = await fetch(`${API_BASE_URL}/api/v1/campaigns`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${getToken()}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(data)
    });
    return response.json();
  },

  // Launch campaign
  async launchCampaign(campaignId: string) {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/campaigns/${campaignId}/launch`,
      {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      }
    );
    return response.json();
  },

  // Get analytics
  async getCampaignAnalytics(campaignId: string) {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/campaigns/${campaignId}/analytics`,
      {
        headers: {
          'Authorization': `Bearer ${getToken()}`
        }
      }
    );
    return response.json();
  }
};
```

### Example React Component

```tsx
import { useState, useEffect } from 'react';
import { campaignApi } from '@/lib/api/campaign-api';

export function CampaignsPage() {
  const [campaigns, setCampaigns] = useState([]);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    const data = await campaignApi.listCampaigns();
    setCampaigns(data.campaigns);
  };

  const launchCampaign = async (id: string) => {
    await campaignApi.launchCampaign(id);
    loadCampaigns();
  };

  return (
    <div>
      <h1>Campaigns</h1>
      {campaigns.map(campaign => (
        <div key={campaign.id}>
          <h3>{campaign.name}</h3>
          <p>Type: {campaign.campaign_type}</p>
          <p>Status: {campaign.status}</p>
          <p>Sent: {campaign.sent_count} / {campaign.target_count}</p>

          {campaign.status === 'draft' && (
            <button onClick={() => launchCampaign(campaign.id)}>
              Launch Campaign
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
```

## 🔐 Environment Variables Required

Add to your `.env` file:

```bash
# SMS (Arkesel)
ARKESEL_API_KEY=your_arkesel_api_key
ARKESEL_SENDER_ID=YourBrand

# WhatsApp
WHATSAPP_API_KEY=your_whatsapp_key
WHATSAPP_PHONE_NUMBER_ID=your_phone_id

# Voice (Vapi)
VAPI_API_KEY=your_vapi_api_key

# Email
SMTP_HOST=mail.ailabsafrica.com
SMTP_PORT=587
SMTP_USERNAME=noreply@yourdomain.com
SMTP_PASSWORD=your_smtp_password
SMTP_FROM_EMAIL=noreply@yourdomain.com
```

## 🧪 Testing

### Create a Test Campaign

```python
import asyncio
from shared.services.unified_campaign_service import UnifiedCampaignService
from shared.services.contact_service import ContactService
from shared.models.campaign import CampaignCreate, CampaignType, MessageTemplate
from shared.models.contact import ContactCreate, ContactType

async def test_campaign():
    # Setup
    db = get_database()
    campaign_service = UnifiedCampaignService(db)
    contact_service = ContactService(db)

    # Create test contact
    contact = await contact_service.create_contact(
        ContactCreate(
            first_name="Test",
            last_name="User",
            email="test@example.com",
            phone="+233241234567",
            contact_type=ContactType.LEAD
        ),
        organization_id="test_org"
    )

    # Create SMS campaign
    campaign = await campaign_service.create_campaign(
        CampaignCreate(
            name="Test SMS Campaign",
            campaign_type=CampaignType.SMS,
            message_template=MessageTemplate(
                text_content="Hello {{first_name}}, this is a test message!"
            )
        ),
        organization_id="test_org",
        user_id="test_user"
    )

    # Launch campaign
    await campaign_service.launch_campaign(campaign.id, "test_org")

    # Wait for completion
    await asyncio.sleep(10)

    # Get analytics
    analytics = await campaign_service.get_campaign_analytics(
        campaign.id,
        "test_org"
    )

    print(f"Campaign Results:")
    print(f"  Sent: {analytics.sent}")
    print(f"  Delivered: {analytics.delivered}")
    print(f"  Failed: {analytics.failed}")
    print(f"  Total Cost: GHS {analytics.total_cost}")

# Run test
asyncio.run(test_campaign())
```

## 📊 Use Cases by App

### EstateFlow (Real Estate)

```python
# Property viewing campaign
campaign = CampaignCreate(
    name="New Listings Alert",
    campaign_type=CampaignType.WHATSAPP,
    message_template=MessageTemplate(
        text_content="Hi {{name}}, we have {{count}} new {{property_type}} properties in {{location}} within your budget!"
    ),
    segment_filter=SegmentFilter(
        tags=["active-buyer"],
        custom_filters={
            "budget_min": 300000,
            "budget_max": 600000,
            "location_preference": "Accra"
        }
    )
)
```

### ChurchFlow (Church Management)

```python
# Sunday service reminder
campaign = CampaignCreate(
    name="Service Reminder",
    campaign_type=CampaignType.SMS,
    message_template=MessageTemplate(
        text_content="Hi {{first_name}}, join us this Sunday at {{service_time}}. Topic: {{sermon_topic}}"
    ),
    segment_filter=SegmentFilter(
        tags=["active-member"],
        custom_filters={
            "membership_status": "active",
            "preferred_service": "main"
        }
    )
)
```

### StudyFlow (Education)

```python
# Exam reminder campaign
campaign = CampaignCreate(
    name="Exam Reminders",
    campaign_type=CampaignType.EMAIL,
    message_template=MessageTemplate(
        subject="Upcoming Exam: {{subject}}",
        html_content="<h1>Don't forget!</h1><p>Your {{subject}} exam is on {{exam_date}}</p>"
    ),
    segment_filter=SegmentFilter(
        tags=["enrolled"],
        custom_filters={
            "grade_level": 12,
            "exam_registered": True
        }
    )
)
```

### EventFlow (Event Management)

```python
# Event invitation campaign
campaign = CampaignCreate(
    name="Tech Conference Invite",
    campaign_type=CampaignType.VOICE,
    message_template=MessageTemplate(
        voice_id="vapi_assistant_123"  # Pre-configured Vapi assistant
    ),
    segment_filter=SegmentFilter(
        tags=["tech-professional", "past-attendee"]
    )
)
```

## 🚀 Advanced Features

### Custom Segmentation

Add app-specific filters in `custom_data`:

```python
segment_filter = SegmentFilter(
    tags=["premium-customer"],
    custom_filters={
        # App-specific fields
        "lifetime_value": {"$gte": 10000},
        "last_purchase_days": {"$lte": 30},
        "subscription_tier": "platinum"
    }
)
```

### Scheduled Campaigns

```python
from datetime import datetime, timedelta

campaign_data = CampaignCreate(
    name="Weekend Sale",
    campaign_type=CampaignType.EMAIL,
    message_template=template,
    schedule_config=ScheduleConfig(
        scheduled_start=datetime.now() + timedelta(days=2),
        business_hours_only=True,
        business_hours_start="09:00",
        business_hours_end="18:00",
        exclude_weekends=False
    )
)
```

### Rate Limiting

```python
delivery_config = DeliveryConfig(
    max_concurrent=20,          # Max 20 messages at once
    rate_per_second=5.0,        # 5 messages per second
    batch_size=100,             # Process 100 at a time
    max_retries=3,              # Retry failed messages 3 times
    retry_delay_seconds=120     # Wait 2 minutes between retries
)
```

## 📚 API Reference

See complete API documentation at `/api/v1/docs` (FastAPI auto-docs) after integration.

### Key Endpoints:

**Campaigns:**
- `POST /api/v1/campaigns` - Create campaign
- `GET /api/v1/campaigns` - List campaigns
- `GET /api/v1/campaigns/{id}` - Get campaign
- `PATCH /api/v1/campaigns/{id}` - Update campaign
- `DELETE /api/v1/campaigns/{id}` - Delete campaign
- `POST /api/v1/campaigns/{id}/launch` - Launch campaign
- `POST /api/v1/campaigns/{id}/pause` - Pause campaign
- `POST /api/v1/campaigns/preview-segment` - Preview segment
- `GET /api/v1/campaigns/{id}/analytics` - Get analytics

**Contacts:**
- `POST /api/v1/campaigns/contacts` - Create contact
- `GET /api/v1/campaigns/contacts` - List contacts
- `GET /api/v1/campaigns/contacts/{id}` - Get contact
- `PATCH /api/v1/campaigns/contacts/{id}` - Update contact
- `DELETE /api/v1/campaigns/contacts/{id}` - Delete contact
- `POST /api/v1/campaigns/contacts/import` - Import CSV
- `GET /api/v1/campaigns/contacts/stats` - Get statistics

## 🎓 Best Practices

1. **Always preview segments** before launching to avoid mistakes:
   ```python
   preview = await campaign_service.preview_segment(
       organization_id=org_id,
       segment_filter=filter,
       campaign_type=CampaignType.SMS
   )
   print(f"Will send to {preview.contact_count} contacts")
   print(f"Estimated cost: GHS {preview.estimated_cost}")
   ```

2. **Use custom_data for app-specific fields**:
   ```python
   contact.custom_data = {
       "property_preferences": ["apartment", "villa"],
       "budget_range": [300000, 600000],
       "viewing_history": [...]
   }
   ```

3. **Respect opt-outs**:
   ```python
   segment_filter = SegmentFilter(
       exclude_opted_out=True  # Always use this!
   )
   ```

4. **Monitor costs**:
   ```python
   analytics = await campaign_service.get_campaign_analytics(campaign_id, org_id)
   if analytics.total_cost > 100:
       # Send alert
       pass
   ```

5. **Test with small segments first**:
   ```python
   # Start with a small test
   test_filter = SegmentFilter(tags=["test-group"])

   # Then scale to full audience
   production_filter = SegmentFilter(tags=["all-customers"])
   ```

## 🆘 Troubleshooting

### Campaign not sending

1. Check service status:
   ```python
   campaign_service._init_delivery_services()
   # Check logs for initialization errors
   ```

2. Verify environment variables are set

3. Check contact has required channel info:
   - SMS/Voice: `phone` field required
   - Email: `email` field required
   - WhatsApp: `whatsapp_number` or `phone` required

### No contacts in segment

Preview the segment to see match count:
```python
preview = await campaign_service.preview_segment(org_id, filter, type)
print(f"Matched contacts: {preview.contact_count}")
print(f"Sample: {preview.sample_contacts}")
```

### Import failing

Check CSV format:
```csv
first_name,last_name,email,phone,tags
John,Doe,john@example.com,+233241234567,interested
```

Required columns: `first_name`, `last_name`, `email` OR `phone`

## 📞 Support

For issues or questions:
- Check logs: `sudo journalctl -u kasaai-{app}-backend -f`
- Review error messages in campaign analytics
- Test individual services (SMS, Email) separately
- Verify database connectivity

## 🎉 You're Ready!

Your app now has enterprise-grade campaign functionality. Start creating campaigns!

```python
# Your first campaign
campaign = await campaign_service.create_campaign(...)
await campaign_service.launch_campaign(campaign.id, org_id)
```

---

**Version**: 1.0
**Last Updated**: December 8, 2025
**Maintained By**: AI Labs Africa
