# Asterisk Phone System Integration

**Internal Documentation - AI Labs Africa Employees Only**

Last Updated: 2025-11-12

## Overview

The Asterisk PBX integration provides virtual phone number provisioning and SIP-based call routing for voice assistants. This system enables developers to provision phone numbers through the API and have incoming calls automatically routed to their voice assistants via webhooks.

## System Architecture

### Components

```
┌────────────────────────────────────────────────────────┐
│                    Developer API                        │
│          (https://api.ailabsafrica.com)                │
│                                                         │
│  POST /api/phone-numbers/provision                     │
│  GET  /api/phone-numbers                               │
│  DELETE /api/phone-numbers/{id}                        │
└──────────────┬──────────────────────────────────────────┘
               │ REST API Call
               ▼
┌────────────────────────────────────────────────────────┐
│         Asterisk REST API (Port 30040)                 │
│    https://asterisk-api.ailabsafrica.com              │
│                                                         │
│  @shared/asterisk_api/                                 │
│   ├─ main.py (FastAPI REST API)                       │
│   ├─ ami_client.py (AMI operations)                   │
│   └─ client.py (Python client library)                │
└──────────────┬──────────────────────────────────────────┘
               │ AMI Protocol (Port 5038)
               ▼
┌────────────────────────────────────────────────────────┐
│         Asterisk PBX (Docker Container)                │
│         kasaai-asterisk-proxy                          │
│                                                         │
│  Config: /opt/kasaai/asterisk/config/                 │
│   ├─ extensions.conf (dialplan)                       │
│   ├─ pjsip_kasaai.conf (SIP peers)                    │
│   ├─ manager.conf (AMI credentials)                   │
│   └─ pjsip.conf (SIP configuration)                   │
│                                                         │
│  AstDB: kasaai/webhook/{number} → webhook_url         │
└──────────────┬──────────────────────────────────────────┘
               │ Incoming SIP Call (Port 5060)
               ▼
┌────────────────────────────────────────────────────────┐
│               Dialplan: kasaai-virtual                 │
│                                                         │
│  1. Answer call                                        │
│  2. Lookup webhook: DB(kasaai/webhook/${NUMBER})      │
│  3. Build JSON payload with call details              │
│  4. POST to webhook via CURL                          │
│  5. Process response (if any)                          │
│  6. Hangup                                             │
└──────────────┬──────────────────────────────────────────┘
               │ HTTP POST Webhook
               ▼
┌────────────────────────────────────────────────────────┐
│            Voice Assistant Endpoint                     │
│   https://api.ailabsafrica.com/voice/webhook/...      │
│                                                         │
│  Receives:                                             │
│  {                                                     │
│    "event": "call.incoming",                           │
│    "call_id": "...",                                   │
│    "caller": {"number": "+233..."},                    │
│    "called": {"number": "+1555..."}                    │
│  }                                                     │
└────────────────────────────────────────────────────────┘
```

## Installation & Setup

### 1. Asterisk Docker Container

Location: `/opt/kasaai/asterisk/`

**Start Container:**
```bash
cd /opt/kasaai/asterisk
docker-compose up -d
```

**Check Status:**
```bash
docker ps | grep kasaai-asterisk-proxy
docker logs kasaai-asterisk-proxy -f
```

**Access Asterisk CLI:**
```bash
docker exec -it kasaai-asterisk-proxy asterisk -rvvv
```

### 2. Asterisk REST API Service

Location: `/opt/kasaai/apps/shared/asterisk_api/`

**Service Configuration:**
```ini
# /etc/systemd/system/kasaai-asterisk-api.service
[Unit]
Description=Kasa AI Asterisk REST API
After=network.target asterisk.service

[Service]
Type=simple
User=dev
Group=dev
WorkingDirectory=/opt/kasaai/apps/shared/asterisk_api
Environment="PYTHONPATH=/opt/kasaai/apps"
EnvironmentFile=/opt/kasaai/.env
ExecStart=/opt/kasaai/apps/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Manage Service:**
```bash
# Start service
sudo systemctl start kasaai-asterisk-api

# Check status
sudo systemctl status kasaai-asterisk-api

# View logs
sudo journalctl -u kasaai-asterisk-api -f

# Restart
sudo systemctl restart kasaai-asterisk-api
```

### 3. Configuration Files

#### AMI Configuration

**File:** `/opt/kasaai/asterisk/config/manager.conf`

```ini
[general]
enabled = yes
port = 5038
bindaddr = 127.0.0.1

[kasaai]
secret = kasaai_secure_ami_password_2025
deny = 0.0.0.0/0.0.0.0
permit = 127.0.0.1/255.255.255.0
read = all
write = all
```

#### Dialplan Configuration

**File:** `/opt/kasaai/asterisk/config/extensions.conf`

Key context: `kasaai-virtual` (lines 63-102)

```
[kasaai-virtual]
exten => _X.,1,NoOp(Incoming call to virtual number ${EXTEN})
same => n,Set(WEBHOOK_URL=${DB(kasaai/webhook/${EXTEN})})
same => n,GotoIf($["${WEBHOOK_URL}" = ""]?no_webhook:has_webhook)
same => n(has_webhook),Answer()
same => n,Set(JSON_PAYLOAD={"event":"call.incoming",...})
same => n,Set(WEBHOOK_RESPONSE=${CURL(${WEBHOOK_URL},${JSON_PAYLOAD})})
same => n,Hangup()
```

#### PJSIP Configuration

**File:** `/opt/kasaai/asterisk/config/pjsip_kasaai.conf`

Dynamically generated SIP peer configurations:

```ini
[production_test_001]
type=endpoint
context=kasaai-virtual
auth=production_test_001-auth
aors=production_test_001-aor
disallow=all
allow=ulaw
allow=alaw
allow=opus

[production_test_001-auth]
type=auth
auth_type=userpass
username=production_test_001
password=secure_prod_pass

[production_test_001-aor]
type=aor
max_contacts=5
qualify_frequency=60
```

## Operations

### Provisioning a Phone Number

**Via Core Backend API:**

```python
from apps.shared.asterisk_api.client import AsteriskAPIClient

# Initialize client
asterisk = AsteriskAPIClient()

# Provision number
response = await asterisk.create_sip_peer(
    number="+15551234567",
    sip_username="kasaai_20251112120000",
    sip_password="secure_generated_password",
    webhook_url="https://api.ailabsafrica.com/voice/webhook/assistant_123",
    context="kasaai-virtual"
)

print(f"Success: {response['success']}")
print(f"SIP Credentials: {response['sip_credentials']}")
```

**What Happens:**

1. **PJSIP Configuration Created**
   - File written to `/opt/kasaai/asterisk/config/pjsip_kasaai.conf`
   - Three sections: endpoint, auth, aor
   - PJSIP module reloaded

2. **Webhook Stored in AstDB**
   - Key: `kasaai/webhook/+15551234567`
   - Value: `https://api.ailabsafrica.com/voice/webhook/assistant_123`

3. **SIP Peer Active**
   - Number can now receive calls
   - Incoming calls routed to `kasaai-virtual` context
   - Webhook invoked for each call

### Verifying Configuration

**Check SIP Peer:**
```bash
docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show endpoint kasaai_20251112120000"
```

**Check AstDB Webhook:**
```bash
docker exec kasaai-asterisk-proxy asterisk -rx "database get kasaai webhook/+15551234567"
```

**List All Webhooks:**
```bash
docker exec kasaai-asterisk-proxy asterisk -rx "database show kasaai/webhook"
```

**View Dialplan:**
```bash
docker exec kasaai-asterisk-proxy asterisk -rx "dialplan show kasaai-virtual"
```

### Deleting a Phone Number

**Via REST API:**

```python
from apps.shared.asterisk_api.client import AsteriskAPIClient

asterisk = AsteriskAPIClient()

response = await asterisk.delete_sip_peer(
    number="+15551234567",
    sip_username="kasaai_20251112120000"
)

print(f"Deleted: {response['success']}")
```

**What Happens:**

1. **SIP Peer Removed**
   - Configuration removed from `pjsip_kasaai.conf`
   - PJSIP module reloaded

2. **Webhook Deleted**
   - Entry removed from AstDB: `kasaai/webhook/+15551234567`

3. **Number Deactivated**
   - Can no longer receive calls
   - SIP registration rejected

## Incoming Call Flow

### Step-by-Step Process

1. **Call Received** (SIP Port 5060)
   ```
   From: +233244123456
   To: +15551234567
   ```

2. **Dialplan Execution** (`kasaai-virtual` context)
   ```
   1. Answer call
   2. Set CALLED_NUMBER=+15551234567
   3. Set CALLER_NUMBER=+233244123456
   4. Lookup WEBHOOK_URL from AstDB
   ```

3. **Webhook Invocation** (CURL function)
   ```json
   POST https://api.ailabsafrica.com/voice/webhook/assistant_123
   Content-Type: application/json

   {
     "event": "call.incoming",
     "call_id": "1731419234.123",
     "caller": {
       "number": "+233244123456"
     },
     "called": {
       "number": "+15551234567"
     },
     "timestamp": "2025-11-12T13:30:00Z"
   }
   ```

4. **Voice Assistant Processing**
   - Receives webhook POST
   - Initiates WebRTC/SIP connection
   - Handles conversation with AI

5. **Call Termination**
   - Assistant ends call or user hangs up
   - Call recording saved (if enabled)
   - Statistics updated in database

### Monitoring Calls in Real-Time

**Watch Asterisk Console:**
```bash
docker exec -it kasaai-asterisk-proxy asterisk -rvvv
```

You'll see output like:
```
[2025-11-12 13:30:00] -- Executing [15551234567@kasaai-virtual:1] NoOp("PJSIP/trunk-00000001", "Incoming call to virtual number 15551234567") in new stack
[2025-11-12 13:30:00] -- Executing [15551234567@kasaai-virtual:2] Set("PJSIP/trunk-00000001", "WEBHOOK_URL=https://api.ailabsafrica.com/voice/webhook/assistant_123") in new stack
[2025-11-12 13:30:00] -- Executing [15551234567@kasaai-virtual:3] Answer("PJSIP/trunk-00000001", "") in new stack
```

## Troubleshooting

### Problem: Asterisk API Returns 503

**Symptom:**
```json
{
  "error": "AMI client not available"
}
```

**Solution:**
```bash
# Check if Asterisk is running
docker ps | grep kasaai-asterisk-proxy

# Check AMI connection
telnet localhost 5038

# Verify AMI credentials in /opt/kasaai/asterisk/config/manager.conf

# Restart services
docker restart kasaai-asterisk-proxy
sudo systemctl restart kasaai-asterisk-api
```

### Problem: Calls Not Reaching Webhook

**Symptom:** Calls connect but webhook never receives POST request

**Debugging:**

1. **Check Webhook is Stored:**
   ```bash
   docker exec kasaai-asterisk-proxy asterisk -rx "database show kasaai/webhook"
   ```

2. **Watch Dialplan Execution:**
   ```bash
   docker exec -it kasaai-asterisk-proxy asterisk -rvvv
   ```

3. **Test Webhook Manually:**
   ```bash
   curl -X POST https://api.ailabsafrica.com/voice/webhook/assistant_123 \
     -H "Content-Type: application/json" \
     -d '{"event":"call.incoming","call_id":"test"}'
   ```

4. **Check Asterisk Logs:**
   ```bash
   docker logs kasaai-asterisk-proxy | grep CURL
   ```

### Problem: SIP Peer Not Registering

**Symptom:** Phone number provisioned but can't receive calls

**Solution:**

1. **Verify PJSIP Configuration:**
   ```bash
   docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show endpoints"
   ```

2. **Check Configuration File:**
   ```bash
   cat /opt/kasaai/asterisk/config/pjsip_kasaai.conf
   ```

3. **Reload PJSIP:**
   ```bash
   docker exec kasaai-asterisk-proxy asterisk -rx "module reload res_pjsip"
   ```

4. **Test SIP Connection:**
   ```bash
   docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show endpoint production_test_001"
   ```

## Integration for New Apps

### Backend Integration

Any KasaAI app can provision phone numbers by importing the shared library:

```python
# In your app's service
from apps.shared.asterisk_api.client import AsteriskAPIClient

class YourPhoneService:
    def __init__(self):
        self.asterisk_client = AsteriskAPIClient()

    async def provision_number_for_assistant(
        self,
        assistant_id: str,
        country_code: str = "+1"
    ):
        # Generate unique SIP credentials
        sip_username = f"app_{uuid4().hex[:12]}"
        sip_password = secrets.token_urlsafe(16)
        webhook_url = f"https://your-app.com/webhook/{assistant_id}"

        # Provision via Asterisk API
        response = await self.asterisk_client.create_sip_peer(
            number=f"{country_code}555{random.randint(1000000, 9999999)}",
            sip_username=sip_username,
            sip_password=sip_password,
            webhook_url=webhook_url
        )

        return response
```

### Frontend Components

Phone management UI components available in b2c-portal:

```
apps/b2c-portal/src/components/phone/
├── PhoneTestingPanel.tsx     # Generate test numbers
├── ImportModal.tsx            # Import from providers
├── ProvisionModal.tsx         # Provision new numbers
└── PhoneNumbersList.tsx       # Manage numbers
```

To use in your app:
1. Copy components to your app
2. Or move to `@shared/frontend/components/phone/` for reuse

## Security

### Best Practices

1. **AMI Access**
   - Bind to localhost only (127.0.0.1)
   - Use strong 32+ character passwords
   - Rotate passwords every 90 days

2. **SIP Credentials**
   - Generate secure passwords (16+ chars)
   - Use `secrets.token_urlsafe(16)`
   - Never log passwords

3. **Webhook URLs**
   - Always use HTTPS
   - Validate webhook responses
   - Implement rate limiting

4. **Firewall Rules**
   - SIP port (5060) open to telecom providers only
   - AMI port (5038) localhost only
   - REST API (30040) internal network only

### Credentials Storage

**Location:** `/opt/kasaai/.env`

```bash
# Asterisk AMI
ASTERISK_AMI_HOST=127.0.0.1
ASTERISK_AMI_PORT=5038
ASTERISK_AMI_USER=kasaai
ASTERISK_AMI_SECRET=kasaai_secure_ami_password_2025

# Asterisk API
ASTERISK_API_URL=https://asterisk-api.ailabsafrica.com
```

## Monitoring & Maintenance

### Health Checks

**Asterisk API:**
```bash
curl https://asterisk-api.ailabsafrica.com/health
```

**Asterisk PBX:**
```bash
docker exec kasaai-asterisk-proxy asterisk -rx "core show version"
docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show endpoints"
```

### Logs

**Asterisk API Logs:**
```bash
sudo journalctl -u kasaai-asterisk-api -f
```

**Asterisk PBX Logs:**
```bash
docker logs kasaai-asterisk-proxy -f
```

**Dialplan Debug:**
```bash
docker exec -it kasaai-asterisk-proxy asterisk -rvvv
```

### Backup

**Configuration Backup:**
```bash
tar -czf asterisk-config-backup-$(date +%Y%m%d).tar.gz \
  /opt/kasaai/asterisk/config/
```

**AstDB Backup:**
```bash
docker exec kasaai-asterisk-proxy asterisk -rx "database show" > astdb-backup-$(date +%Y%m%d).txt
```

## Performance

### Current Capacity

- **Concurrent Calls:** 100+ (tested)
- **SIP Peers:** 1000+ supported
- **API Response Time:** <100ms average
- **Webhook Latency:** ~50ms

### Scaling Considerations

If call volume exceeds 100 concurrent:
1. Add more Asterisk containers (load balanced)
2. Upgrade server CPU/RAM
3. Implement SIP proxy (Kamailio/OpenSIPS)
4. Use external SIP trunk provider

## Documentation

### Available Docs

1. **Developer Platform API:** `/opt/kasaai/apps/developer_platform/API_DOCUMENTATION.md`
   - Section: Phone Numbers API
   - Public-facing API documentation

2. **Shared Library:** `/opt/kasaai/apps/shared/asterisk_api/`
   - `README.md` - API usage and examples
   - `INTEGRATION_REFERENCE.md` - Component reference

3. **Asterisk Config:** `/opt/kasaai/asterisk/`
   - `DIALPLAN_GUIDE.md` - Dialplan configuration
   - `config/extensions.conf` - Actual dialplan

4. **Core Backend:** `/opt/kasaai/apps/core_backend/`
   - `ASTERISK_INTEGRATION_PLAN.md` - Implementation plan

### Quick Reference Links

- API Docs: https://docs.ailabsafrica.com/api-reference/phone-numbers
- Swagger UI: https://asterisk-api.ailabsafrica.com/docs
- ReDoc: https://asterisk-api.ailabsafrica.com/redoc

## Support

### Internal Team Contacts

- **Primary:** Dev Team (dev@ailabsafrica.com)
- **Architecture:** System Architecture Team
- **Operations:** DevOps Team

### Escalation Path

1. Check logs (Asterisk API + PBX)
2. Review documentation above
3. Test manually with curl
4. Contact dev team with logs

---

**Document Version:** 1.0
**Last Reviewed:** 2025-11-12
**Next Review:** 2026-01-12
