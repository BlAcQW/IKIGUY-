# ChurchFlow - Shared Services & Infrastructure Usage

**Version:** 1.0
**Date:** 2025-10-24
**Status:** Production Configuration

---

## Overview

ChurchFlow leverages KasaAI's shared infrastructure and services to avoid reinventing the wheel. This document outlines all shared services, local infrastructure, and integration points.

---

## Authentication & Storage

### Supabase (Local Instance)

**Endpoint**: https://supabase.ailabsafrica.com

**Services Used**:
- **Supabase Auth** - Phone OTP authentication, JWT generation
- **Supabase Storage** - Profile photos, conference banners, speaker photos
- **Supabase PostgreSQL + pgvector** - RAG embeddings for member search (Phase 2)

**Configuration**:
```python
# In churchflow/backend/.env
SUPABASE_URL="https://supabase.ailabsafrica.com"
SUPABASE_KEY="<anon_key>"  # Get from Supabase dashboard
SUPABASE_SERVICE_ROLE_KEY="<service_role_key>"
```

**Usage**:
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Send OTP
await supabase.auth.sign_in_with_otp({"phone": "+233201234567"})

# Verify OTP
session = await supabase.auth.verify_otp({
    "phone": "+233201234567",
    "token": "123456",
    "type": "sms"
})

# Upload file
await supabase.storage.from_("churchflow-images").upload(
    path=f"profiles/{user_id}.jpg",
    file=image_bytes
)
```

**Migration Needed**: ✅ Update .env to use local instance

---

## Notification Services

### Push Notifications (NO FIREBASE - Use Supabase Realtime or WebSockets)

**Important**: We do NOT use Firebase Cloud Messaging. Instead:

**Option 1: Supabase Realtime** (Recommended)
- Uses WebSocket connections
- Built into Supabase
- No additional service needed

```typescript
// In mobile app
const channel = supabase
  .channel('churchflow-notifications')
  .on('broadcast', { event: 'notification' }, (payload) => {
    showNotification(payload.data)
  })
  .subscribe()
```

**Option 2: Native Push via n8n + OneSignal** (If native push needed)
- Use OneSignal (free tier: 10K subscribers)
- Integrate with n8n workflows

**Configuration**:
```python
# No Firebase config needed
# Use WebSocket endpoint instead
WS_URL="wss://supabase.ailabsafrica.com/realtime/v1"
```

---

### SMS Notifications (Twilio via n8n)

**Service**: Twilio SMS
**Orchestration**: n8n workflows

**Configuration**:
```python
# In .env
TWILIO_ACCOUNT_SID="<from_n8n_credentials>"
TWILIO_AUTH_TOKEN="<from_n8n_credentials>"
TWILIO_PHONE_NUMBER="+1234567890"
```

**Usage** (via n8n):
```python
from apps.shared.integration.n8n import N8NIntegration

n8n = N8NIntegration()

await n8n.execute_workflow_webhook(
    workflow_name="churchflow/bus-delay",
    data={
        "phone": "+233201234567",
        "message": "Bus Legon #1 delayed 30 min..."
    }
)
```

---

### Email Notifications (Local iRedMail)

**Service**: iRedMail (self-hosted, local server)
**Endpoint**: `mail.ailabsafrica.com` or local SMTP

**Configuration**:
```python
# In churchflow/backend/.env
SMTP_HOST="mail.ailabsafrica.com"  # Or localhost if same server
SMTP_PORT=587  # or 465 for SSL
SMTP_USERNAME="churchflow@ailabsafrica.com"
SMTP_PASSWORD="<password>"
SMTP_FROM_EMAIL="churchflow@ailabsafrica.com"
SMTP_FROM_NAME="ChurchFlow"
SMTP_USE_TLS=True
```

**Usage**:
```python
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def send_email(to: str, subject: str, body_html: str):
    msg = MIMEMultipart('alternative')
    msg['From'] = f"{SMTP_FROM_NAME} <{SMTP_FROM_EMAIL}>"
    msg['To'] = to
    msg['Subject'] = subject

    html_part = MIMEText(body_html, 'html')
    msg.attach(html_part)

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        if SMTP_USE_TLS:
            server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
```

**Email Templates**:
```python
templates = {
    "conference_registration": """
    <h2>You're Registered for {conference_name}!</h2>
    <p>Hi {user_name},</p>
    <p>Your registration for <strong>{conference_name}</strong> is confirmed.</p>
    <p><strong>Details:</strong></p>
    <ul>
        <li>Date: {conference_date}</li>
        <li>Venue: {venue}</li>
        <li>Your Bus: {bus_name} at {bus_time}</li>
    </ul>
    <p>Your QR code is attached to this email.</p>
    """,

    "bus_delay": """
    <h2>Bus Delay Update</h2>
    <p>Hi {user_name},</p>
    <p>Your bus <strong>{bus_name}</strong> has been delayed by {delay_minutes} minutes.</p>
    <p><strong>New departure time:</strong> {new_time}</p>
    <p>We apologize for the inconvenience.</p>
    """
}
```

**Migration Needed**: ✅ Remove SendGrid references, use local SMTP

---

## AI Services (from @apps/shared/integration/)

### 1. Voice AI - VAPI (Phase 2)

**Service**: `@apps/shared/integration/vapi.py`
**Endpoint**: https://api.vapi.ai
**Use Case**: Phone calls for surveys, kiosk voice interface

**Configuration**:
```python
VAPI_API_KEY="<from_kasaai_credentials>"
```

**Usage**:
```python
from apps.shared.integration.vapi import VAPIIntegration

vapi = VAPIIntegration()

# Create AI assistant for kiosk
assistant = await vapi.create_assistant(
    name="Ama - ChurchFlow Kiosk",
    system_prompt="You are Ama, a warm Ghanaian AI assistant...",
    voice="jennifer",
    first_message="Akwaaba! Welcome to Impact 2025..."
)

# Start kiosk interaction
call = await vapi.create_web_call(
    assistant_id=assistant.id,
    metadata={"conference_id": str(conf.id)}
)
```

---

### 2. RAG - Gemini 2.5 Flash (Phase 2)

**Service**: `@apps/shared/integration/rag.py`
**Provider**: Google Gemini 2.5 Flash (via API)
**Use Case**: Semantic member search, context for personalized greetings

**Configuration**:
```python
GOOGLE_API_KEY="<from_kasaai_credentials>"
GEMINI_MODEL="gemini-2.5-flash"
```

**Usage**:
```python
from apps.shared.integration.rag import RAGService

rag = RAGService(
    collection_name="churchflow_members",
    provider="gemini",
    model_name="gemini-2.5-flash"
)

# Ingest member profile
await rag.ingest_document(
    content=f"{user.name} from {user.branch}, serves as {user.roles}",
    metadata={"user_id": str(user.id), "name": user.name}
)

# Query during kiosk interaction
results = await rag.query(
    query=f"Who is {voice_input} from {branch}?",
    top_k=3
)
```

**Storage**: Supabase PostgreSQL with pgvector extension

---

### 3. AI Provider Services (Phase 2)

**Service**: `@apps/shared/integration/ai_services/`
**Use Case**: TTS for kiosk voice output

**Providers Available**:
- **Coqui XTTS** (https://coqui.ailabsafrica.com) - 17 languages, voice cloning
- **MeloTTS** (https://melotts.ailabsafrica.com) - 6 languages, fast
- **F5-TTS** (https://f5tts.ailabsafrica.com) - 4 languages, voice cloning

**Usage**:
```python
from apps.shared.integration.ai_services import AIProviderService, ProviderType

tts_service = AIProviderService(provider_type=ProviderType.TTS)

# Generate speech for greeting
audio = await tts_service.request(
    provider_name="coqui_xtts",
    text="Hi Akosua from Legon branch! It's always a joy to see you.",
    parameters={"language": "en", "voice": "female_ghanaian"}
)

# Play audio on kiosk
await play_audio(audio.audio_data)
```

---

### 4. n8n Workflow Orchestration

**Service**: `@apps/shared/integration/n8n.py`
**Endpoint**: https://n8n.ailabsafrica.com
**Use Case**: Multi-channel notification routing

**Configuration**:
```python
N8N_API_URL="https://n8n.ailabsafrica.com"
N8N_API_KEY="<from_kasaai_credentials>"
```

**Workflow Example**:
```python
from apps.shared.integration.n8n import N8NIntegration

n8n = N8NIntegration()

# Create workflow for bus delay notifications
workflow = await n8n.create_workflow(
    name="ChurchFlow - Bus Delay Multi-Channel",
    trigger={"type": "webhook", "path": "churchflow/bus-delay"},
    nodes=[
        {
            "type": "switch",
            "condition": "delay_minutes >= 30",
            "branches": {
                "true": ["sms_node", "whatsapp_node"],
                "false": ["websocket_node"]
            }
        },
        {
            "id": "sms_node",
            "type": "twilio_sms",
            "message": "Bus {{$json.bus_name}} delayed {{$json.delay_minutes}} min..."
        },
        {
            "id": "websocket_node",
            "type": "http_request",
            "method": "POST",
            "url": "https://supabase.ailabsafrica.com/realtime/v1/broadcast",
            "body": {
                "event": "notification",
                "payload": "={{$json}}"
            }
        }
    ]
)
```

---

### 5. Wallet Service (Optional - Phase 3)

**Service**: `@apps/shared/integration/wallet.py`
**Use Case**: Track AI service usage for billing (when SaaS)

**Configuration**:
```python
WALLET_ENABLED=False  # Disable for MVP
```

**Usage** (Phase 3):
```python
from apps.shared.integration.wallet import WalletService

wallet = WalletService()

# Track TTS usage
await wallet.deduct(
    user_id=str(user.id),
    amount=0.01,  # $0.01 per TTS call
    operation="tts_synthesis",
    metadata={"provider": "coqui_xtts", "text_length": 150}
)
```

---

## Database & Storage

### MongoDB (Primary Database)

**Endpoint**: localhost:27017 (or remote if configured)
**Database**: `churchflow_db`

**Collections**:
- `users`
- `branches`
- `conferences`
- `bus_routes`
- `bus_registrations`
- `conference_registrations`
- `notification_logs`

**Configuration**:
```python
MONGODB_URL="mongodb://localhost:27017"
MONGODB_DATABASE="churchflow_db"
```

---

### Supabase PostgreSQL (for RAG - Phase 2)

**Endpoint**: Included in Supabase instance
**Extension**: pgvector

**Setup**:
```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create embeddings table
CREATE TABLE churchflow_member_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    embedding VECTOR(1536),
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Create index for fast similarity search
CREATE INDEX ON churchflow_member_embeddings
USING ivfflat (embedding vector_cosine_ops);
```

---

## Infrastructure

### Nginx (Reverse Proxy)

**Config File**: `/etc/nginx/sites-available/church.kasaai.ailabsafrica.com.conf`

**Configuration**:
```nginx
server {
    listen 80;
    server_name church.kasaai.ailabsafrica.com;

    location / {
        proxy_pass http://127.0.0.1:8000;  # FastAPI backend
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /ws {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

---

### Systemd (Service Management)

**Service File**: `/etc/systemd/system/kasaai-churchflow.service`

```ini
[Unit]
Description=ChurchFlow FastAPI Backend
After=network.target

[Service]
User=dev
Group=dev
WorkingDirectory=/opt/kasaai/apps/churchflow/backend
Environment="PATH=/opt/kasaai/apps/venv/bin"
ExecStart=/opt/kasaai/apps/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000

[Install]
WantedBy=multi-user.target
```

**Commands**:
```bash
sudo systemctl enable kasaai-churchflow
sudo systemctl start kasaai-churchflow
sudo systemctl status kasaai-churchflow
```

---

## Summary: What We Use

### MVP (Phase 1)
✅ **Supabase** (local) - Auth, Storage
✅ **MongoDB** (local) - Primary database
✅ **n8n** (shared) - Notification orchestration
✅ **Twilio** (via n8n) - SMS
✅ **iRedMail** (local) - Email
✅ **Supabase Realtime** - Push notifications (WebSocket)
✅ **Nginx** - Reverse proxy
✅ **Systemd** - Service management

### Phase 2 (AI Features)
✅ **VAPI** (shared) - Voice AI for kiosk
✅ **RAG** (shared) - Gemini 2.5 Flash for context
✅ **AI Services** (shared) - TTS (Coqui, Melo, F5)
✅ **pgvector** (Supabase) - Embeddings storage

### NOT Used
❌ **Firebase** - Using Supabase Realtime instead
❌ **SendGrid** - Using local iRedMail
❌ **AWS/GCP** - Self-hosted on VPS

---

## Configuration Checklist

Before running ChurchFlow, ensure:

- [ ] Supabase local instance accessible at `https://supabase.ailabsafrica.com`
- [ ] MongoDB running on localhost:27017
- [ ] n8n accessible (for notification workflows)
- [ ] iRedMail SMTP configured
- [ ] Twilio credentials added to n8n
- [ ] Nginx config created and enabled
- [ ] Systemd service file created
- [ ] SSL certificate installed (Let's Encrypt)
- [ ] Environment variables set in `/opt/kasaai/apps/churchflow/backend/.env`

---

## Next Steps

1. ✅ Update churchflow backend `.env` to use local services
2. ✅ Test Supabase Auth with phone OTP
3. ✅ Configure iRedMail SMTP
4. ✅ Set up n8n workflows for notifications
5. ✅ Deploy backend and test end-to-end flow

---

**End of Document**
