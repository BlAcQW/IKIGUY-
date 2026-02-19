# Asterisk Integration - Component Reference

## Overview

The Asterisk integration is **fully centralized in `@shared/asterisk_api/`** for backend operations. Frontend components are currently in `b2c-portal` but can be moved to `@shared/frontend/components/` for reusability across apps.

## 📦 Centralized Backend Components

### Location: `/opt/kasaai/apps/shared/asterisk_api/`

All backend Asterisk integration is centralized and accessible to all KasaAI apps:

#### 1. **REST API Service** (`main.py`)
- **Port**: 30040
- **URL**: https://asterisk-api.ailabsafrica.com
- **Status**: ✅ Running (kasaai-asterisk-api.service)
- **Purpose**: HTTP wrapper for Asterisk AMI operations

**Endpoints:**
```
GET  /health                 - Health check
POST /sip/peer              - Create SIP peer
DELETE /sip/peer            - Delete SIP peer
GET  /sip/peer/{username}   - Get peer status
GET  /sip/peers             - List all peers
POST /call/route            - Create call route
GET  /asterisk/status       - Asterisk status
POST /asterisk/reload       - Reload PJSIP
```

#### 2. **AMI Client** (`ami_client.py`)
- **Purpose**: Low-level Asterisk Manager Interface operations
- **Library**: panoramisk (async AMI client)
- **Features**:
  - SIP peer creation/deletion
  - PJSIP configuration file management
  - AstDB webhook storage
  - Asterisk status monitoring

#### 3. **Python Client Library** (`client.py`)
- **Purpose**: Easy-to-use client for other Python apps
- **Class**: `AsteriskAPIClient`
- **Usage**:
```python
from apps.shared.asterisk_api.client import AsteriskAPIClient

client = AsteriskAPIClient(base_url="https://asterisk-api.ailabsafrica.com")

# Create SIP peer
response = await client.create_sip_peer(
    number="+15551234567",
    sip_username="assistant_001",
    sip_password="secure_pass",
    webhook_url="https://api.ailabsafrica.com/voice/webhook/assistant_001"
)

# Delete SIP peer
await client.delete_sip_peer(
    number="+15551234567",
    sip_username="assistant_001"
)

# Check health
health = await client.health_check()
```

## 🎨 Frontend Components (Currently in b2c-portal)

### Location: `/opt/kasaai/apps/b2c-portal/src/components/phone/`

These components are currently app-specific but can be moved to `@shared/frontend/components/phone/` for reusability:

### 1. **PhoneTestingPanel.tsx**
- **Purpose**: Generate test phone numbers and shareable UI links
- **Features**:
  - Uses FastRTC `.fastphone()` for test numbers
  - Uses `.ui.launch()` for shareable UI links
  - Copy-to-clipboard functionality
  - Widget-style UI (Vapi pattern)

**Props:**
```typescript
interface PhoneTestingPanelProps {
  assistantId: string;
  assistantName: string;
}
```

**Usage:**
```tsx
import { PhoneTestingPanel } from '@/components/phone/PhoneTestingPanel';

<PhoneTestingPanel
  assistantId={assistant.id}
  assistantName={assistant.name}
/>
```

### 2. **ImportModal.tsx**
- **Purpose**: Import phone numbers from providers (Twilio, Vonage, etc.)
- **Features**:
  - Multi-provider support
  - Credential validation
  - Testing functionality
  - Error handling
  - Documentation links

**Usage:**
```tsx
import { ImportModal } from '@/components/phone/ImportModal';

<ImportModal
  isOpen={isOpen}
  onClose={handleClose}
  onImport={handleImport}
/>
```

### 3. **ProvisionModal.tsx**
- **Purpose**: Provision new virtual phone numbers
- **Features**:
  - Country/area code selection
  - Provider selection (Kasa AI, Twilio, Vonage)
  - Plan selection
  - Real-time availability checking

### 4. **PhoneNumbersList.tsx**
- **Purpose**: Display and manage provisioned phone numbers
- **Features**:
  - List view with provider badges
  - Status indicators
  - Edit/delete actions
  - Search and filtering

## 🔌 Integration Points

### Backend Integration (Core Backend)

**File**: `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/phone_numbers.py`

```python
from apps.shared.asterisk_api.client import AsteriskAPIClient

class PhoneNumberService:
    def __init__(self):
        # Initialize Asterisk client
        asterisk_api_url = os.getenv("ASTERISK_API_URL", "https://asterisk-api.ailabsafrica.com")
        self.asterisk_client = AsteriskAPIClient(base_url=asterisk_api_url)

    async def _register_with_asterisk(self, phone_number: PhoneNumber):
        """Register virtual number with Asterisk"""
        response = await self.asterisk_client.create_sip_peer(
            number=phone_number.number,
            sip_username=phone_number.sip_username,
            sip_password=phone_number.sip_password,
            webhook_url=phone_number.webhook_url
        )
        return response.get("success")

    async def _unregister_from_asterisk(self, phone_number: PhoneNumber):
        """Unregister virtual number from Asterisk"""
        await self.asterisk_client.delete_sip_peer(
            number=phone_number.number,
            sip_username=phone_number.sip_username
        )
```

### Dialplan Integration

**File**: `/opt/kasaai/asterisk/config/extensions.conf`

```
[kasaai-virtual]
exten => _X.,1,NoOp(Incoming call to virtual number ${EXTEN})
same => n,Set(WEBHOOK_URL=${DB(kasaai/webhook/${CALLED_NUMBER})})
same => n,Set(WEBHOOK_RESPONSE=${CURL(${WEBHOOK_URL},${JSON_PAYLOAD})})
same => n,Playback(demo-thanks)
same => n,Hangup()
```

**Documentation**: `/opt/kasaai/asterisk/DIALPLAN_GUIDE.md`

## 🏗️ Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                    KasaAI Applications                       │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Core Backend │  │  Developer   │  │  Other Apps  │     │
│  │   (30027)    │  │   Platform   │  │              │     │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘     │
│         │                 │                 │              │
│         └─────────────────┴─────────────────┘              │
│                           │                                │
│         ┌─────────────────▼─────────────────┐             │
│         │  @shared/asterisk_api/client.py   │             │
│         │  (Python Client Library)          │             │
│         └─────────────────┬─────────────────┘             │
└───────────────────────────┼───────────────────────────────┘
                            │ HTTPS
                            │
            ┌───────────────▼────────────────┐
            │  Asterisk REST API (30040)     │
            │  @shared/asterisk_api/main.py  │
            │  https://asterisk-api...       │
            └───────────────┬────────────────┘
                            │ AMI (5038)
                            │
            ┌───────────────▼────────────────┐
            │  Asterisk PBX (Docker)         │
            │  - PJSIP Configuration         │
            │  - kasaai-virtual Context      │
            │  - Webhook Routing (AstDB)     │
            └────────────────────────────────┘
                            │
                            │ Webhook HTTP POST
                            │
            ┌───────────────▼────────────────┐
            │  Voice Assistants              │
            │  - VAPI                        │
            │  - Custom Assistants           │
            └────────────────────────────────┘
```

## 🔐 Environment Configuration

### Backend Apps

Add to your app's environment (e.g., `/opt/kasaai/.env`):

```bash
# Asterisk API
ASTERISK_API_URL=https://asterisk-api.ailabsafrica.com

# Optional: For apps that need direct AMI access
ASTERISK_AMI_HOST=127.0.0.1
ASTERISK_AMI_PORT=5038
ASTERISK_AMI_USER=kasaai
ASTERISK_AMI_SECRET=kasaai_secure_ami_password_2025
```

### Frontend Apps

Add to your app's API configuration:

```typescript
// config/api-config.ts
export const API_ENDPOINTS = {
  asterisk: {
    base: 'https://asterisk-api.ailabsafrica.com',
    health: '/health',
    sipPeer: '/sip/peer',
    callRoute: '/call/route',
  },
  // ... other endpoints
};
```

## 📚 Available Documentation

All documentation is centralized in `@shared/asterisk_api/`:

1. **README.md** - Complete API documentation, endpoints, examples
2. **INTEGRATION_REFERENCE.md** (this file) - Component reference and architecture
3. `/opt/kasaai/asterisk/DIALPLAN_GUIDE.md` - Dialplan configuration and testing
4. `/opt/kasaai/apps/core_backend/ASTERISK_INTEGRATION_PLAN.md` - Implementation plan

## ✅ Currently Integrated Apps

### 1. Core Backend (Port 30027)
- **Status**: ✅ Fully Integrated
- **Features**:
  - Phone number provisioning
  - SIP peer registration
  - Webhook management
  - Real-time testing
- **API Endpoints**:
  - `POST /api/phone-numbers/provision`
  - `GET /api/phone-numbers`
  - `DELETE /api/phone-numbers/{id}`

### 2. B2C Portal
- **Status**: ✅ Frontend Components Available
- **Features**:
  - Phone testing panel
  - Import modal
  - Provision modal
  - Phone numbers list

## 🎯 How Other Apps Can Use It

### Backend Integration (Python)

**Step 1**: Import the client
```python
from apps.shared.asterisk_api.client import AsteriskAPIClient
```

**Step 2**: Initialize in your service
```python
class MyVoiceService:
    def __init__(self):
        self.asterisk_client = AsteriskAPIClient()
```

**Step 3**: Use the client
```python
async def provision_number(self, number: str):
    response = await self.asterisk_client.create_sip_peer(
        number=number,
        sip_username=f"app_{uuid4().hex[:12]}",
        sip_password=secrets.token_urlsafe(16),
        webhook_url=f"https://myapp.ailabsafrica.com/webhook"
    )
    return response
```

### Frontend Integration (TypeScript/React)

**Option 1**: Copy components from b2c-portal
```bash
cp -r /opt/kasaai/apps/b2c-portal/src/components/phone \
      /opt/kasaai/apps/your-app/src/components/
```

**Option 2**: Move to shared and import (recommended)
```bash
# Move to shared
mv /opt/kasaai/apps/b2c-portal/src/components/phone \
   /opt/kasaai/apps/shared/frontend/components/phone

# Export from shared/frontend/components/index.ts
export * from './phone/PhoneTestingPanel';
export * from './phone/ImportModal';
export * from './phone/ProvisionModal';

# Import in your app
import { PhoneTestingPanel } from '@kasaai/shared-frontend/components';
```

**Option 3**: Direct API calls
```typescript
import { API_ENDPOINTS } from '@/config/api-config';

async function createSIPPeer(number: string) {
  const response = await fetch(`${API_ENDPOINTS.asterisk.base}/sip/peer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      number,
      sip_username: `app_${Date.now()}`,
      sip_password: generatePassword(),
      webhook_url: `${API_ENDPOINTS.voice.base}/webhook`,
      context: 'kasaai-virtual'
    })
  });
  return response.json();
}
```

## 🚀 Quick Start for New Apps

### Backend (Python/FastAPI)

1. **Install dependencies** (already in shared venv):
```bash
# httpx is already installed
```

2. **Import and use**:
```python
# your-app/backend/services/phone_service.py
from apps.shared.asterisk_api.client import AsteriskAPIClient

asterisk = AsteriskAPIClient()

async def setup_phone(number: str, webhook_url: str):
    return await asterisk.create_sip_peer(
        number=number,
        sip_username=f"myapp_{uuid4().hex[:10]}",
        sip_password=secrets.token_urlsafe(16),
        webhook_url=webhook_url
    )
```

### Frontend (React/TypeScript)

1. **Add API config**:
```typescript
// src/config/api-config.ts
export const ASTERISK_API = 'https://asterisk-api.ailabsafrica.com';
```

2. **Create API client**:
```typescript
// src/lib/asterisk-client.ts
export async function createSIPPeer(params: CreatePeerParams) {
  const response = await fetch(`${ASTERISK_API}/sip/peer`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params)
  });
  return response.json();
}
```

3. **Use in components**:
```tsx
import { createSIPPeer } from '@/lib/asterisk-client';

function MyComponent() {
  const handleProvision = async () => {
    const result = await createSIPPeer({
      number: '+15551234567',
      sip_username: 'test_001',
      sip_password: 'secure_pass',
      webhook_url: 'https://myapp.com/webhook'
    });
    console.log('SIP peer created:', result);
  };

  return <button onClick={handleProvision}>Provision Number</button>;
}
```

## 📊 Component Accessibility Summary

| Component | Location | Accessible To | Status |
|-----------|----------|---------------|--------|
| REST API Service | `@shared/asterisk_api/main.py` | ✅ All Apps (HTTP) | Running (30040) |
| AMI Client | `@shared/asterisk_api/ami_client.py` | ✅ All Python Apps | Stable |
| Python Client | `@shared/asterisk_api/client.py` | ✅ All Python Apps | Stable |
| PhoneTestingPanel | `b2c-portal/components/phone/` | ⚠️ b2c-portal only | Can be moved |
| ImportModal | `b2c-portal/components/phone/` | ⚠️ b2c-portal only | Can be moved |
| ProvisionModal | `b2c-portal/components/phone/` | ⚠️ b2c-portal only | Can be moved |
| PhoneNumbersList | `b2c-portal/components/phone/` | ⚠️ b2c-portal only | Can be moved |

## 🔧 Services Status

```bash
# Check all services
sudo systemctl status kasaai-asterisk-api
docker ps | grep kasaai-asterisk-proxy
sudo systemctl status kasaai-core-backend

# Test API
curl https://asterisk-api.ailabsafrica.com/health

# Test dialplan
docker exec kasaai-asterisk-proxy asterisk -rx "dialplan show kasaai-virtual"

# View webhooks
docker exec kasaai-asterisk-proxy asterisk -rx "database show kasaai/webhook"
```

## 📝 Next Steps for Full Centralization

To make frontend components accessible to all apps:

1. **Move phone components to shared**:
```bash
mv /opt/kasaai/apps/b2c-portal/src/components/phone \
   /opt/kasaai/apps/shared/frontend/components/
```

2. **Export from shared/frontend/components/index.ts**:
```typescript
export * from './phone/PhoneTestingPanel';
export * from './phone/ImportModal';
export * from './phone/ProvisionModal';
export * from './phone/PhoneNumbersList';
```

3. **Update package.json** in apps that need it:
```json
{
  "dependencies": {
    "@kasaai/shared-frontend": "file:../../shared/frontend"
  }
}
```

4. **Import in any app**:
```tsx
import {
  PhoneTestingPanel,
  ImportModal,
  ProvisionModal
} from '@kasaai/shared-frontend/components';
```

## 🆘 Support

For integration help:
- **Backend**: Check `@shared/asterisk_api/README.md`
- **Dialplan**: Check `/opt/kasaai/asterisk/DIALPLAN_GUIDE.md`
- **API Docs**: https://asterisk-api.ailabsafrica.com/docs
- **Logs**: `sudo journalctl -u kasaai-asterisk-api -f`

---

**Last Updated**: 2025-11-12
**Version**: 1.0.0
**Maintained By**: AI Labs Africa Dev Team
