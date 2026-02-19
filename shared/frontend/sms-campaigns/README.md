# Shared SMS Campaign Components

Reusable React components for SMS campaign management across all AI Labs Africa applications.

## Features

- ✅ Campaign analytics dashboard with 4 tabs (Overview, Successful, Failed, All Messages)
- ✅ Real-time progress tracking
- ✅ Message-level details with error reporting
- ✅ Responsive design with Tailwind CSS
- ✅ TypeScript support
- ✅ Centralized in `@shared/` for use across all apps

## Components

### `SMSCampaignAnalytics`

Main analytics modal component that displays comprehensive campaign statistics and message details.

**Props:**
```typescript
interface SMSCampaignAnalyticsProps {
  campaign: SMSCampaign | null;      // Campaign data
  isOpen: boolean;                    // Modal visibility
  onClose: () => void;                // Close handler
  apiBaseUrl: string;                 // API endpoint base URL
  authToken: string;                  // Authentication token
  onAction?: (action, id) => void;    // Optional action handler
}
```

## Installation in Your App

### 1. Copy Component Files

```bash
# The component is already in @shared/frontend/sms-campaigns/
# No need to copy - just import!
```

### 2. Install Required Dependencies

Your app needs these dependencies:
```bash
npm install lucide-react
```

### 3. Import in Your Page/Component

```typescript
// In your SMS Campaigns page (e.g., src/pages/SMSCampaigns.tsx)
import { SMSCampaignAnalytics } from '../../../shared/frontend/sms-campaigns/SMSCampaignAnalytics';
```

### 4. Use the Component

```tsx
export const SMSCampaignsPage = () => {
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const token = localStorage.getItem('access_token');

  const handleCampaignClick = (campaign) => {
    setSelectedCampaign(campaign);
    setShowAnalytics(true);
  };

  const handleAction = async (action, campaignId) => {
    // Handle start, pause, edit, duplicate actions
    if (action === 'start') {
      await fetch(`${API_BASE_URL}/sms-campaigns/${campaignId}/start`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      // Refresh campaign list
    }
  };

  return (
    <div>
      {/* Your campaign list */}
      <table>
        {campaigns.map(campaign => (
          <tr onClick={() => handleCampaignClick(campaign)}>
            <td>{campaign.name}</td>
            <td>{campaign.status}</td>
          </tr>
        ))}
      </table>

      {/* Analytics Modal */}
      <SMSCampaignAnalytics
        campaign={selectedCampaign}
        isOpen={showAnalytics}
        onClose={() => setShowAnalytics(false)}
        apiBaseUrl="https://api.ailabsafrica.com"
        authToken={token}
        onAction={handleAction}
      />
    </div>
  );
};
```

## Backend Requirements

Your backend must expose these endpoints:

### 1. Get Campaign Messages
```
GET /sms-campaigns/{id}/messages?status={status}&limit={limit}&skip={skip}

Response:
{
  "messages": [
    {
      "id": "...",
      "recipient_name": "John Doe",
      "recipient_phone": "+233...",
      "recipient_email": "...",
      "status": "sent|failed|pending|delivered",
      "error_message": "...",
      "sent_at": "...",
      "cost": 0.05
    }
  ],
  "total": 5000,
  "summary": {
    "sent": 3000,
    "failed": 100,
    "pending": 1900
  },
  "pagination": {
    "limit": 100,
    "skip": 0,
    "has_more": true
  }
}
```

### 2. Get Campaign Details
```
GET /sms-campaigns/{id}

Response: SMSCampaign object
```

### 3. Campaign Actions (Optional)
```
POST /sms-campaigns/{id}/start
POST /sms-campaigns/{id}/pause
PUT /sms-campaigns/{id}
```

## Apps Currently Using This

- ✅ **ChurchFlow** - Conference/event SMS notifications
- ✅ **B2C Portal** - Customer engagement campaigns
- 🚧 **StudyFlow** - Student notifications (planned)
- 🚧 **EventFlow** - Event reminders (planned)
- 🚧 **InkWave** - Audiobook updates (planned)

## Styling

The component uses Tailwind CSS classes. Ensure your app has Tailwind configured with these classes available:
- `bg-indigo-*`, `bg-purple-*`, `bg-green-*`, `bg-red-*`, `bg-yellow-*`
- `text-*`, `rounded-*`, `flex`, `grid`
- Standard spacing (`p-*`, `m-*`, `gap-*`)

## TypeScript Types

```typescript
export interface SMSCampaign {
  id: string;
  name: string;
  template_content: string;
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'failed' | 'cancelled';
  progress: {
    total_recipients: number;
    sent: number;
    delivered: number;
    failed: number;
    pending: number;
  };
  total_cost: number;
  sms_provider: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export interface CampaignMessage {
  id: string;
  recipient_name: string;
  recipient_phone: string;
  recipient_email?: string;
  status: 'sent' | 'failed' | 'pending' | 'delivered';
  error_message?: string;
  sent_at?: string;
  failed_at?: string;
  cost?: number;
}
```

## Customization

The component is designed to be used as-is, but you can fork it for app-specific customizations:

1. **Colors**: Modify the gradient and badge colors in the JSX
2. **Actions**: Pass custom `onAction` handler for app-specific workflows
3. **Tabs**: Add/remove tabs by modifying the tab state and rendering logic
4. **Fields**: Add extra fields to the overview or message tables

## Support

For issues or questions:
1. Check the backend SMS campaign service documentation in `@shared/services/sms_campaign_service.py`
2. Review integration examples in ChurchFlow (`apps/churchflow/frontend/src/pages/SMSCampaigns.tsx`)
3. Contact the platform team

## Version History

- **v1.0** (Dec 2025) - Initial release with full analytics dashboard
  - 4-tab interface
  - Message-level tracking
  - Error reporting
  - Responsive design
