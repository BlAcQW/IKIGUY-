# Shared Campaign Frontend Components

**Complete, plug-and-play React components for multi-channel campaign management.**

Supports Voice (Vapi), SMS (Arkesel), WhatsApp, and Email campaigns with the centralized campaign backend system.

## 🎯 What's Included

### Components:
1. **`CampaignList`** - Campaign dashboard with filters, launch controls, and analytics access
2. **`CampaignAnalytics`** - Comprehensive analytics modal for all campaign types
3. **`ContactList`** - Contact/lead management with import, filters, and stats

### Features:
- ✅ Multi-channel support (Voice, SMS, WhatsApp, Email)
- ✅ Real-time campaign progress tracking
- ✅ Launch and pause campaigns
- ✅ Detailed analytics with delivery/open/click rates
- ✅ Contact management with CSV import
- ✅ Advanced filtering and search
- ✅ Responsive design with Tailwind CSS
- ✅ TypeScript support
- ✅ Works with centralized backend router

## 📦 Installation

### 1. Install Dependencies

```bash
npm install lucide-react
```

### 2. Import Components

```typescript
import { CampaignList, CampaignAnalytics, ContactList } from '@shared/frontend/campaigns';
```

## 🚀 Usage Examples

### Campaign List Component

Display all campaigns with launch controls:

```tsx
import { CampaignList } from '@shared/frontend/campaigns';
import { useState } from 'react';

export function CampaignsPage() {
  const [selectedCampaign, setSelectedCampaign] = useState(null);
  const [showAnalytics, setShowAnalytics] = useState(false);
  const token = localStorage.getItem('access_token');

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">Marketing Campaigns</h1>

      <CampaignList
        apiBaseUrl="https://api.example.com"
        authToken={token}
        onCampaignClick={(campaign) => {
          setSelectedCampaign(campaign);
          setShowAnalytics(true);
        }}
        onLaunch={(id) => {
          console.log('Campaign launched:', id);
        }}
        onCreateNew={() => {
          // Navigate to campaign creation wizard
        }}
      />

      {selectedCampaign && (
        <CampaignAnalytics
          campaignId={selectedCampaign.id}
          apiBaseUrl="https://api.example.com"
          authToken={token}
          isOpen={showAnalytics}
          onClose={() => setShowAnalytics(false)}
        />
      )}
    </div>
  );
}
```

### Campaign Analytics Component

Show detailed analytics for a campaign:

```tsx
import { CampaignAnalytics } from '@shared/frontend/campaigns';

<CampaignAnalytics
  campaignId="campaign_123"
  apiBaseUrl="https://api.example.com"
  authToken={token}
  isOpen={showModal}
  onClose={() => setShowModal(false)}
/>
```

### Contact List Component

Manage contacts with import and filtering:

```tsx
import { ContactList } from '@shared/frontend/campaigns';

<ContactList
  apiBaseUrl="https://api.example.com"
  authToken={token}
  onContactClick={(contact) => {
    console.log('Contact clicked:', contact);
  }}
  onCreateNew={() => {
    // Open contact creation dialog
  }}
  onImportSuccess={() => {
    console.log('Contacts imported successfully!');
  }}
/>
```

## 🎨 Complete Example Page

Full campaign management page:

```tsx
import React, { useState } from 'react';
import {
  CampaignList,
  CampaignAnalytics,
  ContactList
} from '@shared/frontend/campaigns';
import type { Campaign } from '@shared/frontend/campaigns';

export function CampaignManagementPage() {
  const [activeTab, setActiveTab] = useState<'campaigns' | 'contacts'>('campaigns');
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [showAnalytics, setShowAnalytics] = useState(false);

  const token = localStorage.getItem('access_token');
  const apiBaseUrl = import.meta.env.VITE_API_BASE_URL;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto p-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-3xl font-bold text-gray-900">
            Campaign Management
          </h1>
          <p className="text-gray-600 mt-2">
            Multi-channel marketing campaigns and contact management
          </p>
        </div>

        {/* Tabs */}
        <div className="border-b border-gray-200 mb-6">
          <nav className="-mb-px flex gap-6">
            <button
              onClick={() => setActiveTab('campaigns')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'campaigns'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Campaigns
            </button>
            <button
              onClick={() => setActiveTab('contacts')}
              className={`py-4 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'contacts'
                  ? 'border-indigo-500 text-indigo-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Contacts
            </button>
          </nav>
        </div>

        {/* Content */}
        {activeTab === 'campaigns' ? (
          <CampaignList
            apiBaseUrl={apiBaseUrl}
            authToken={token}
            onCampaignClick={(campaign) => {
              setSelectedCampaign(campaign);
              setShowAnalytics(true);
            }}
            onLaunch={(id) => {
              console.log('Campaign launched:', id);
            }}
            onCreateNew={() => {
              // Navigate to campaign wizard
            }}
          />
        ) : (
          <ContactList
            apiBaseUrl={apiBaseUrl}
            authToken={token}
            onContactClick={(contact) => {
              console.log('Contact clicked:', contact);
            }}
            onCreateNew={() => {
              // Open contact creation form
            }}
            onImportSuccess={() => {
              console.log('Import successful!');
            }}
          />
        )}

        {/* Analytics Modal */}
        {selectedCampaign && (
          <CampaignAnalytics
            campaignId={selectedCampaign.id}
            apiBaseUrl={apiBaseUrl}
            authToken={token}
            isOpen={showAnalytics}
            onClose={() => {
              setShowAnalytics(false);
              setSelectedCampaign(null);
            }}
          />
        )}
      </div>
    </div>
  );
}
```

## 🔧 Component Props

### CampaignList

```typescript
interface CampaignListProps {
  apiBaseUrl: string;              // API base URL
  authToken: string;                // Auth token for API calls
  organizationId?: string;          // Optional organization filter
  onCampaignClick?: (campaign: Campaign) => void;  // Campaign click handler
  onLaunch?: (campaignId: string) => void;         // Launch success handler
  onCreateNew?: () => void;         // Create button handler
}
```

### CampaignAnalytics

```typescript
interface CampaignAnalyticsProps {
  campaignId: string;               // Campaign ID to show analytics for
  apiBaseUrl: string;               // API base URL
  authToken: string;                // Auth token
  isOpen: boolean;                  // Modal visibility
  onClose: () => void;              // Close handler
}
```

### ContactList

```typescript
interface ContactListProps {
  apiBaseUrl: string;               // API base URL
  authToken: string;                // Auth token
  onContactClick?: (contact: Contact) => void;  // Contact click handler
  onCreateNew?: () => void;         // Create button handler
  onImportSuccess?: () => void;     // Import success handler
}
```

## 📊 Data Types

### Campaign

```typescript
interface Campaign {
  id: string;
  name: string;
  campaign_type: 'voice' | 'sms' | 'whatsapp' | 'email';
  status: 'draft' | 'scheduled' | 'running' | 'paused' | 'completed' | 'cancelled' | 'failed';
  target_count: number;
  sent_count: number;
  delivered_count: number;
  failed_count: number;
  total_cost: number;
  currency: string;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}
```

### Contact

```typescript
interface Contact {
  id: string;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  contact_type: 'lead' | 'customer' | 'prospect' | 'member' | 'student' | 'attendee';
  interest_level: 'hot' | 'warm' | 'cold' | 'unqualified';
  tags: string[];
  segments: string[];
  opt_out_channels: string[];
  total_campaigns_sent: number;
  total_campaigns_opened: number;
  created_at: string;
}
```

## 🎨 Styling

Components use Tailwind CSS classes. Ensure your app has these configured:

```js
// tailwind.config.js
module.exports = {
  content: [
    './src/**/*.{js,jsx,ts,tsx}',
    '../../../shared/frontend/**/*.{js,jsx,ts,tsx}' // Include shared components
  ],
  theme: {
    extend: {
      colors: {
        // Ensure these color variants are available
        indigo: { ... },
        blue: { ... },
        green: { ... },
        red: { ... },
        purple: { ... },
        orange: { ... },
        yellow: { ... }
      }
    }
  }
}
```

## 🔐 Backend Requirements

Your backend must have the centralized campaign router mounted:

```python
# backend/app/api/__init__.py
from shared.routers.campaign_router import get_campaign_router

campaign_router = get_campaign_router(
    get_database_func=get_database,
    get_current_user_func=get_current_user,
    get_org_context_func=get_organization_context
)

app.include_router(campaign_router, prefix="/api/v1")
```

See `CAMPAIGN_INTEGRATION_GUIDE.md` in `@shared/services/` for full backend setup.

## 📱 Mobile Responsive

All components are fully responsive:
- Desktop: Full table layout with all columns
- Tablet: Condensed view with essential columns
- Mobile: Card-based layout (if you customize further)

## 🔄 Real-time Updates

For real-time campaign progress:

```tsx
import { useState, useEffect } from 'react';

function CampaignPage() {
  const [campaign, setCampaign] = useState(null);

  // Poll for updates every 5 seconds
  useEffect(() => {
    const interval = setInterval(async () => {
      const response = await fetch(`${apiBaseUrl}/api/v1/campaigns/${id}`);
      const data = await response.json();
      setCampaign(data);
    }, 5000);

    return () => clearInterval(interval);
  }, [id]);

  // ... render
}
```

## 🛠️ Customization

### Colors

Modify campaign type colors:

```tsx
// In CampaignList.tsx
const getCampaignTypeColor = (type: CampaignType) => {
  return {
    voice: 'bg-purple-100 text-purple-800',  // Change these
    sms: 'bg-blue-100 text-blue-800',
    whatsapp: 'bg-green-100 text-green-800',
    email: 'bg-orange-100 text-orange-800'
  }[type];
};
```

### Additional Columns

Add custom columns to tables:

```tsx
// In ContactList.tsx, add to <thead>
<th>Custom Field</th>

// Add to <tbody>
<td>{contact.custom_data?.yourField}</td>
```

## 📚 Apps Using These Components

- ✅ **EstateFlow** - Property campaign management
- ✅ **ChurchFlow** - Member communications
- 🚧 **StudyFlow** - Student notifications (planned)
- 🚧 **EventFlow** - Event marketing (planned)
- 🚧 **InkWave** - Book promotions (planned)

## 🐛 Troubleshooting

### Components not rendering?

1. Check Tailwind CSS is configured with shared path
2. Verify lucide-react is installed
3. Check API endpoints are accessible

### Authentication errors?

1. Verify token is valid: `console.log(authToken)`
2. Check CORS settings on backend
3. Verify Authorization header format

### Styling issues?

1. Ensure Tailwind processes shared component files
2. Check color variants are configured
3. Verify no CSS conflicts

## 📖 Related Documentation

- [Backend Integration Guide](/opt/kasaai/apps/shared/services/CAMPAIGN_INTEGRATION_GUIDE.md)
- [Campaign Models](/opt/kasaai/apps/shared/models/campaign.py)
- [Contact Models](/opt/kasaai/apps/shared/models/contact.py)
- [Unified Campaign Service](/opt/kasaai/apps/shared/services/unified_campaign_service.py)

## 🆘 Support

For issues or questions:
1. Check backend logs: `sudo journalctl -u kasaai-{app}-backend -f`
2. Verify API responses in browser dev tools
3. Review integration examples in EstateFlow
4. Contact platform team

## 📝 Version History

- **v1.0** (Dec 2025) - Initial release
  - CampaignList component
  - CampaignAnalytics component
  - ContactList component
  - Full TypeScript support
  - Multi-channel support

---

**Built by AI Labs Africa**
**Version**: 1.0
**Last Updated**: December 8, 2025
