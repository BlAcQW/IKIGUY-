# WhatsApp Campaign System - Implementation Guide

## Overview

This document outlines the implementation of a centralized WhatsApp campaign system using WhatsApp Business API. The system follows the same architectural patterns as the existing SMS and voice campaign systems, providing consistent APIs and user experience across all campaign types.

## Architecture

### Design Principles
1. **Centralization**: Core functionality in `@shared/` for reuse across all apps
2. **Consistency**: Same patterns as SMS/voice campaigns for familiar developer experience
3. **Full Integration**: Complete analytics, cost tracking, and delivery monitoring
4. **Feature-Rich**: Templates, media, interactive buttons, and delivery tracking

### System Components

```
@shared/
├── services/
│   └── whatsapp_campaign_service.py    # Core campaign management
├── integration/
│   ├── whatsapp_business.py            # Existing WhatsApp Business API client
│   └── whatsapp.py                      # Basic WhatsApp integration
└── WHATSAPP_CAMPAIGN_INTEGRATION_GUIDE.md

@core_backend/
└── backend/
    ├── api/
    │   └── routes/
    │       └── whatsapp_campaigns.py    # API endpoints
    └── main.py                          # Service registration

@b2c-portal/
└── src/
    ├── pages/
    │   └── campaigns/
    │       └── WhatsAppCampaigns.tsx    # Main UI
    ├── components/
    │   └── whatsapp/
    │       ├── WhatsAppCampaignForm.tsx
    │       ├── WhatsAppTemplateSelector.tsx
    │       ├── WhatsAppMediaUploader.tsx
    │       └── WhatsAppButtonEditor.tsx
    └── lib/
        └── api/
            └── whatsapp-campaigns.ts    # API client

@churchflow/
└── backend/
    └── main.py                          # Import and use service

@studyflow/, @eventflow/, @inkwave/
└── (Future integration following same pattern)
```

## Implementation Plan

### Phase 1: Centralized Service (@shared/)

#### 1.1 WhatsApp Campaign Service
**File**: `@shared/services/whatsapp_campaign_service.py`

**Data Models**:
```python
class WhatsAppCampaignStatus(Enum):
    DRAFT = "draft"
    SCHEDULED = "scheduled"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class WhatsAppMessageStatus(Enum):
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"

@dataclass
class WhatsAppTemplate:
    id: str
    name: str
    language: str
    category: str
    components: List[Dict[str, Any]]
    status: str  # APPROVED, PENDING, REJECTED
    placeholders: List[str]

@dataclass
class WhatsAppCampaignConfig:
    send_rate_per_second: float = 1.0
    batch_size: int = 100
    retry_failed: bool = True
    max_retries: int = 2
    retry_delay_seconds: int = 60
    scheduled_time: Optional[datetime] = None

    # WhatsApp-specific
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    enable_media: bool = False
    media_url: Optional[str] = None
    media_type: Optional[str] = None
    enable_buttons: bool = False
    buttons: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class WhatsAppCampaignProgress:
    total_recipients: int = 0
    sent: int = 0
    delivered: int = 0
    read: int = 0
    failed: int = 0
    pending: int = 0

@dataclass
class WhatsAppCampaign:
    id: str
    name: str
    organization_id: str
    user_id: str

    template_id: Optional[str] = None
    template_name: Optional[str] = None
    template_content: str = ""
    audience_id: Optional[str] = None

    status: WhatsAppCampaignStatus = WhatsAppCampaignStatus.DRAFT
    config: WhatsAppCampaignConfig = field(default_factory=WhatsAppCampaignConfig)
    progress: WhatsAppCampaignProgress = field(default_factory=WhatsAppCampaignProgress)

    # Cost tracking
    total_cost: float = 0.0
    cost_per_message: float = 0.0

    # Timing
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    # Error tracking
    error_message: Optional[str] = None

    # WhatsApp-specific
    whatsapp_business_account_id: str = ""
    phone_number_id: str = ""

@dataclass
class WhatsAppCampaignMessage:
    id: str
    campaign_id: str
    recipient_phone: str
    recipient_name: Optional[str] = None
    recipient_email: Optional[str] = None
    recipient_data: Dict[str, Any] = field(default_factory=dict)

    message_content: str = ""
    template_name: Optional[str] = None
    template_variables: Dict[str, Any] = field(default_factory=dict)

    status: WhatsAppMessageStatus = WhatsAppMessageStatus.PENDING

    # WhatsApp-specific
    provider_message_id: Optional[str] = None
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    read_at: Optional[datetime] = None
    failed_at: Optional[datetime] = None

    # Media
    media_url: Optional[str] = None
    media_id: Optional[str] = None

    # Buttons
    buttons: List[Dict[str, Any]] = field(default_factory=list)

    error_message: Optional[str] = None
    retry_count: int = 0
    cost: float = 0.0

    created_at: datetime = field(default_factory=datetime.utcnow)
```

**Core Methods**:
```python
class WhatsAppCampaignService:
    def __init__(self, db=None, whatsapp_provider=None):
        """Initialize with database and WhatsApp Business API client."""

    # Campaign Management
    async def create_campaign(...) -> WhatsAppCampaign
    async def get_campaign(campaign_id: str) -> Optional[WhatsAppCampaign]
    async def list_campaigns(...) -> List[WhatsAppCampaign]
    async def update_campaign(...) -> Optional[WhatsAppCampaign]
    async def delete_campaign(campaign_id: str) -> bool

    # Template Management
    async def get_templates() -> List[WhatsAppTemplate]
    async def get_template(template_id: str) -> Optional[WhatsAppTemplate]
    async def sync_templates() -> int

    # Message Preparation
    async def prepare_campaign_messages(campaign_id: str, contacts: List[Dict]) -> int

    # Campaign Execution
    async def start_campaign(campaign_id: str) -> bool
    async def pause_campaign(campaign_id: str) -> bool
    async def cancel_campaign(campaign_id: str) -> bool
    async def _execute_campaign(campaign_id: str)

    # Media Handling
    async def upload_media(file_path: str) -> str
    async def get_media(media_id: str) -> WhatsAppMedia

    # Analytics
    async def get_campaign_analytics(campaign_id: str) -> Dict[str, Any]
    async def get_campaign_messages(...) -> List[Dict]

    # Webhooks
    async def process_delivery_status(webhook_data: Dict) -> bool
```

#### 1.2 Integration Enhancement
**File**: `@shared/integration/whatsapp_business.py` (already exists)

Enhancements needed:
- Add cost calculation per message
- Add rate limiting support
- Add batch sending optimization
- Add delivery tracking webhook processing

### Phase 2: Backend API (@core_backend/)

#### 2.1 API Endpoints
**File**: `@core_backend/backend/api/routes/whatsapp_campaigns.py`

```python
# Campaign CRUD
POST   /api/v1/whatsapp-campaigns              # Create campaign
GET    /api/v1/whatsapp-campaigns              # List campaigns
GET    /api/v1/whatsapp-campaigns/{id}         # Get campaign
PUT    /api/v1/whatsapp-campaigns/{id}         # Update campaign
DELETE /api/v1/whatsapp-campaigns/{id}         # Delete campaign

# Campaign Operations
POST   /api/v1/whatsapp-campaigns/{id}/start   # Start campaign
POST   /api/v1/whatsapp-campaigns/{id}/pause   # Pause campaign
POST   /api/v1/whatsapp-campaigns/{id}/cancel  # Cancel campaign

# Templates
GET    /api/v1/whatsapp-campaigns/templates    # List templates
GET    /api/v1/whatsapp-campaigns/templates/{id} # Get template
POST   /api/v1/whatsapp-campaigns/templates/sync # Sync from WhatsApp

# Messages
GET    /api/v1/whatsapp-campaigns/{id}/messages # Get campaign messages
GET    /api/v1/whatsapp-campaigns/{id}/analytics # Get campaign analytics

# Media
POST   /api/v1/whatsapp-campaigns/media/upload  # Upload media
GET    /api/v1/whatsapp-campaigns/media/{id}    # Get media

# Webhooks
POST   /webhooks/whatsapp/status                # Delivery status webhook
POST   /webhooks/whatsapp/messages              # Incoming messages webhook
```

#### 2.2 Database Collections

**MongoDB Collections**:
```
whatsapp_campaigns
  - Campaign documents

whatsapp_campaign_messages
  - Individual message documents
  - Indexed by: campaign_id, status, recipient_phone

whatsapp_templates
  - Cached templates from WhatsApp Business API
  - Indexed by: name, status

whatsapp_media
  - Uploaded media metadata
  - Indexed by: organization_id
```

#### 2.3 Service Integration
**File**: `@core_backend/backend/main.py`

```python
from shared.services.whatsapp_campaign_service import whatsapp_campaign_service
from shared.integration.whatsapp_business import WhatsAppBusinessIntegration, WhatsAppBusinessConfig

# Initialize WhatsApp provider
whatsapp_config = WhatsAppBusinessConfig(
    access_token=settings.WHATSAPP_ACCESS_TOKEN,
    phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID,
    business_account_id=settings.WHATSAPP_BUSINESS_ACCOUNT_ID
)
whatsapp_provider = WhatsAppBusinessIntegration(whatsapp_config)

# Initialize campaign service
whatsapp_campaign_service.set_database(db)
whatsapp_campaign_service.set_whatsapp_provider(whatsapp_provider)
```

### Phase 3: Frontend UI (@b2c-portal/)

#### 3.1 Main Campaign Page
**File**: `@b2c-portal/src/pages/campaigns/WhatsAppCampaigns.tsx`

Features:
- Campaign list with status indicators
- Create/edit campaign modal
- Campaign analytics dashboard
- Real-time progress tracking
- Template selector
- Media uploader
- Button editor

#### 3.2 Components

**WhatsAppCampaignForm.tsx**:
- Campaign name and description
- Audience selector
- Template selector
- Variable mapping
- Media upload (optional)
- Button configuration (optional)
- Scheduling options

**WhatsAppTemplateSelector.tsx**:
- List approved templates
- Preview template with variables
- Template status indicator
- Placeholder mapping UI

**WhatsAppMediaUploader.tsx**:
- File upload with preview
- Supported formats: image, video, audio, document
- Caption editor
- Media library browser

**WhatsAppButtonEditor.tsx**:
- Add/remove buttons (max 3)
- Button types: reply, url, phone
- Button text editor
- Preview

#### 3.3 API Client
**File**: `@b2c-portal/src/lib/api/whatsapp-campaigns.ts`

```typescript
export const whatsappCampaignsAPI = {
  // Campaigns
  createCampaign: (data: CreateWhatsAppCampaignRequest) => Promise<WhatsAppCampaign>
  getCampaigns: (orgId: string) => Promise<WhatsAppCampaign[]>
  getCampaign: (id: string) => Promise<WhatsAppCampaign>
  updateCampaign: (id: string, data: UpdateWhatsAppCampaignRequest) => Promise<WhatsAppCampaign>
  deleteCampaign: (id: string) => Promise<boolean>

  // Operations
  startCampaign: (id: string) => Promise<boolean>
  pauseCampaign: (id: string) => Promise<boolean>
  cancelCampaign: (id: string) => Promise<boolean>

  // Templates
  getTemplates: () => Promise<WhatsAppTemplate[]>
  syncTemplates: () => Promise<number>

  // Analytics
  getCampaignAnalytics: (id: string) => Promise<WhatsAppCampaignAnalytics>
  getCampaignMessages: (id: string, params?: MessageQueryParams) => Promise<WhatsAppMessage[]>

  // Media
  uploadMedia: (file: File) => Promise<string>
}
```

### Phase 4: ChurchFlow Integration

#### 4.1 Backend Integration
**File**: `@churchflow/backend/main.py`

```python
# Import centralized service
from shared.services.whatsapp_campaign_service import whatsapp_campaign_service

# Use in routes
app.include_router(
    whatsapp_campaigns_router,
    prefix="/api/v1/whatsapp-campaigns",
    tags=["WhatsApp Campaigns"]
)
```

#### 4.2 Frontend Integration
- Add WhatsApp campaigns tab in ChurchFlow admin
- Reuse B2C portal components
- Church-specific audience integration (members, leaders, groups)

### Phase 5: Testing

#### 5.1 Unit Tests
**File**: `@shared/tests/test_whatsapp_campaign_service.py`

Tests:
- Campaign CRUD operations
- Template management
- Message preparation
- Campaign execution
- Delivery tracking
- Error handling
- Rate limiting
- Cost calculation

#### 5.2 Integration Tests
**File**: `@core_backend/tests/test_whatsapp_campaigns_api.py`

Tests:
- API endpoint responses
- Authentication/authorization
- Database operations
- Webhook processing
- Real WhatsApp API calls (with test account)

#### 5.3 E2E Tests
- Create campaign via UI
- Upload media
- Configure buttons
- Start campaign
- Monitor progress
- Verify delivery
- Delete campaign

## Configuration

### Environment Variables

```bash
# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_VERIFY_TOKEN=your_webhook_verify_token
WHATSAPP_WEBHOOK_SECRET=your_webhook_secret

# Pricing (adjust based on your WhatsApp Business pricing)
WHATSAPP_COST_PER_MESSAGE=0.0055  # USD per message
WHATSAPP_COST_PER_MEDIA=0.0100    # Additional cost for media
```

### WhatsApp Business Setup

1. **Create WhatsApp Business Account**:
   - Go to Facebook Business Manager
   - Create WhatsApp Business Account
   - Verify business
   - Add phone number

2. **Get API Credentials**:
   - Generate access token
   - Get phone number ID
   - Get business account ID

3. **Configure Templates**:
   - Create message templates
   - Submit for approval
   - Wait for approval (24-48 hours)

4. **Setup Webhooks**:
   - Configure webhook URL: `https://api.ailabsafrica.com/webhooks/whatsapp/status`
   - Set verify token
   - Subscribe to message status updates

## Features

### Supported Features

✅ **Template Messages**:
- Pre-approved templates with variables
- Header, body, footer components
- Multiple language support
- Variable substitution

✅ **Media Support**:
- Images (JPEG, PNG)
- Videos (MP4)
- Audio (MP3, AAC)
- Documents (PDF, DOC, XLS)
- Media captions

✅ **Interactive Buttons**:
- Quick reply buttons (max 3)
- Call-to-action buttons
- URL buttons
- Phone number buttons

✅ **Delivery Tracking**:
- Sent status
- Delivered status
- Read status
- Failed status with reason
- Real-time webhook updates

✅ **Analytics & Reporting**:
- Total sent/delivered/read
- Success rate
- Failure analysis
- Cost tracking
- Time-based analytics

✅ **Campaign Management**:
- Draft campaigns
- Scheduled campaigns
- Pause/resume
- Cancel
- Progress monitoring

### Cost Structure

Based on WhatsApp Business API pricing (example):
- Marketing conversation: $0.0055 per message
- Utility conversation: $0.0020 per message
- Authentication conversation: $0.0045 per message
- Service conversation: Free (24hr window)
- Media: Additional $0.0100 per media file

## Migration Path

### Existing ChurchFlow WhatsApp Integration

ChurchFlow currently uses basic Twilio WhatsApp. Migration steps:

1. **Phase 1**: Run both systems in parallel
2. **Phase 2**: Migrate templates to WhatsApp Business API
3. **Phase 3**: Update ChurchFlow UI to use new campaign system
4. **Phase 4**: Migrate existing data
5. **Phase 5**: Deprecate old integration

## Performance Considerations

### Rate Limiting
- Default: 1 message/second (configurable)
- Business accounts: Up to 1000 messages/second
- Respect WhatsApp rate limits
- Implement exponential backoff

### Optimization
- Batch message preparation
- Async processing
- Connection pooling
- Caching templates
- Media CDN

### Monitoring
- Campaign execution status
- API call metrics
- Error rates
- Cost tracking
- Delivery rates

## Security

### API Security
- Access token rotation
- Webhook signature verification
- Request validation
- Rate limiting
- IP whitelisting (optional)

### Data Privacy
- Phone number encryption
- GDPR compliance
- Opt-out management
- Data retention policies
- Audit logging

## Best Practices

### Template Design
1. Keep messages concise
2. Use clear call-to-action
3. Test with variables
4. Follow WhatsApp guidelines
5. Get approval before campaign

### Campaign Execution
1. Test with small audience first
2. Monitor delivery rates
3. Handle failures gracefully
4. Respect sending hours
5. Track costs

### Error Handling
1. Retry failed messages (with limit)
2. Log all errors
3. Alert on high failure rates
4. Provide clear error messages
5. Support manual intervention

## Timeline

### Implementation Schedule

**Week 1**:
- [ ] Create WhatsApp campaign service
- [ ] Enhance WhatsApp Business integration
- [ ] Setup database collections
- [ ] Write unit tests

**Week 2**:
- [ ] Create API endpoints
- [ ] Setup webhooks
- [ ] Integration tests
- [ ] Documentation

**Week 3**:
- [ ] Build frontend components
- [ ] Create campaign UI
- [ ] Template selector
- [ ] Media uploader

**Week 4**:
- [ ] Integrate with B2C portal
- [ ] Integrate with ChurchFlow
- [ ] E2E testing
- [ ] Production deployment

## Support

### Documentation
- API documentation: `/docs/whatsapp-campaigns`
- User guide: `/docs/user-guides/whatsapp-campaigns`
- Developer guide: This document

### Troubleshooting
- Check WhatsApp Business API status
- Verify access token validity
- Review webhook logs
- Check template approval status
- Monitor rate limits

## Future Enhancements

### Phase 2 Features
- [ ] List messages (interactive menus)
- [ ] Product catalogs
- [ ] Location messages
- [ ] Contact cards
- [ ] Message reactions

### Phase 3 Features
- [ ] AI-powered message generation
- [ ] A/B testing
- [ ] Advanced segmentation
- [ ] Conversation flows
- [ ] Chatbot integration

### Phase 4 Features
- [ ] Multi-language campaigns
- [ ] Smart scheduling
- [ ] Predictive analytics
- [ ] Cost optimization
- [ ] Advanced reporting

## References

- [WhatsApp Business Platform](https://developers.facebook.com/docs/whatsapp)
- [WhatsApp Cloud API](https://developers.facebook.com/docs/whatsapp/cloud-api)
- [Message Templates](https://developers.facebook.com/docs/whatsapp/message-templates)
- [Webhooks](https://developers.facebook.com/docs/whatsapp/cloud-api/webhooks)
- [Pricing](https://developers.facebook.com/docs/whatsapp/pricing)

---

**Document Version**: 1.0
**Last Updated**: 2025-12-02
**Author**: AI Labs Africa Engineering Team
