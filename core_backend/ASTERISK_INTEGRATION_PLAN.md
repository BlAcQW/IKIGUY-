# Asterisk/Kasa AI Phone Number Integration Plan

## Executive Summary

This document outlines the plan to integrate Asterisk PBX with Kasa AI's phone number provisioning system. The goal is to enable real-time SIP peer creation, dialplan configuration, and automatic registration of virtual phone numbers that can be used by voice assistants.

---

## 1. Current State Analysis

### What Exists

✅ **Virtual Number Generation** (`phone_numbers.py:269-345`)
- Country-specific number format generation (Ghana, US/Canada, international)
- Area code handling with realistic prefix selection
- Random number generation with proper formatting

✅ **SIP Credential Creation**
- Unique SIP username generation: `kasaai_{timestamp}`
- Secure password generation using `_generate_secure_password()`
- SIP server configuration: `asterisk.ailabsafrica.com`

✅ **Pricing Tiers**
- Starter: $1/month (1 number, 100 outbound minutes)
- Professional: $5/month (5 numbers, unlimited calls)
- Enterprise: $20/month (20 numbers, unlimited everything)

✅ **Phone Number Model**
- Complete data structure with SIP fields
- Status management (pending → active)
- Webhook URL generation
- Metadata tracking (plan, virtual flag, sip_context)

### What's Missing

❌ **Actual Asterisk Integration**
- Placeholder `_register_with_asterisk()` function exists but doesn't connect to Asterisk
- No Asterisk AMI (Asterisk Manager Interface) client library
- No SIP peer configuration file generation
- No dialplan entry creation
- No configuration reload mechanism

❌ **Asterisk Infrastructure**
- No confirmation that Asterisk is installed on our servers (148.251.0.46 or 85.214.12.174)
- No AMI credentials configured
- No SIP context configuration in Asterisk
- No dialplan for routing calls to voice assistants

❌ **Call Routing**
- No mechanism to route incoming calls to voice assistants
- No webhook invocation when calls are received
- No integration with Vapi or FastRTC for call handling

---

## 2. Integration Architecture

### High-Level Flow

```
User Provisions Number (Frontend)
        ↓
Backend Creates Virtual Number
        ↓
Backend Registers SIP Peer in Asterisk (NEW)
        ↓
Backend Creates Dialplan Entry (NEW)
        ↓
Backend Reloads Asterisk Config (NEW)
        ↓
Number Status → Active
        ↓
Incoming Call → Asterisk
        ↓
Asterisk Executes Dialplan → Webhook (NEW)
        ↓
Webhook Routes to Voice Assistant (FastRTC/Vapi)
```

### Components

1. **Asterisk AMI Client** (Python)
   - Connect to Asterisk Manager Interface
   - Execute commands (create peers, reload configs)
   - Monitor call events

2. **SIP Peer Management**
   - Dynamic peer creation
   - Configuration file generation
   - Peer deletion on number release

3. **Dialplan Management**
   - Dynamic context creation
   - Webhook URL routing
   - Call parameter passing

4. **Call Webhook Handler** (FastAPI)
   - Receive call events from Asterisk
   - Route to assigned voice assistant
   - Integrate with FastRTC/Vapi

---

## 3. Implementation Options

### Option A: Asterisk Manager Interface (AMI) - **RECOMMENDED**

**Pros:**
- Real-time configuration without file changes
- Full programmatic control
- Event monitoring (call status, peer registration)
- No file system access needed
- Battle-tested protocol

**Cons:**
- Requires AMI enabled on Asterisk server
- Need to manage persistent connection
- Slightly more complex than file-based approach

**Python Library:** `panoramisk` (async) or `asterisk-ami-client` (sync)

**Implementation:**
```python
from panoramisk import Manager

async def _register_with_asterisk(self, phone_number: PhoneNumber):
    """Register virtual number with Asterisk via AMI"""
    manager = Manager(
        host='asterisk.ailabsafrica.com',
        port=5038,
        username=os.getenv('ASTERISK_AMI_USER'),
        secret=os.getenv('ASTERISK_AMI_SECRET')
    )

    await manager.connect()

    # Create SIP peer
    await manager.command({
        'Action': 'UpdateConfig',
        'SrcFilename': 'pjsip.conf',
        'DstFilename': 'pjsip.conf',
        'Action-000000': 'NewCat',
        'Cat-000000': phone_number.sip_username,
        'Action-000001': 'Append',
        'Cat-000001': phone_number.sip_username,
        'Var-000001': 'type',
        'Value-000001': 'endpoint',
        'Action-000002': 'Append',
        'Cat-000002': phone_number.sip_username,
        'Var-000002': 'auth',
        'Value-000002': phone_number.sip_username,
        'Action-000003': 'Append',
        'Cat-000003': phone_number.sip_username,
        'Var-000003': 'aors',
        'Value-000003': phone_number.sip_username,
        'Action-000004': 'Append',
        'Cat-000004': phone_number.sip_username,
        'Var-000004': 'context',
        'Value-000004': 'kasaai-virtual'
    })

    # Reload PJSIP
    await manager.command({'Action': 'PJSIPReload'})

    await manager.close()
```

### Option B: REST API (Asterisk HTTP/ARI)

**Pros:**
- Simple HTTP requests
- No persistent connection needed
- Modern REST interface

**Cons:**
- Limited compared to AMI
- May not support all configuration changes
- Need to verify ARI availability on our Asterisk

**Not recommended for initial implementation** - AMI is more complete.

### Option C: File-Based Configuration

**Pros:**
- Simple file writes
- No special Asterisk setup needed

**Cons:**
- Requires file system access to Asterisk server
- Manual reload needed
- Race conditions possible
- Not scalable

**Not recommended** - Too fragile for production.

---

## 4. Detailed Implementation Plan

### Phase 1: Infrastructure Setup (Week 1)

**1.1 Verify Asterisk Installation**
- [ ] SSH to production server (148.251.0.46)
- [ ] Check if Asterisk is installed: `asterisk -V`
- [ ] Check Asterisk status: `sudo systemctl status asterisk`
- [ ] If not installed, install via: `sudo apt install asterisk asterisk-modules`

**1.2 Configure Asterisk AMI**
- [ ] Edit `/etc/asterisk/manager.conf`:
```ini
[general]
enabled = yes
port = 5038
bindaddr = 127.0.0.1  ; Only localhost for security

[kasaai]
secret = <generate-secure-password>
read = all
write = all
```
- [ ] Reload AMI: `sudo asterisk -rx "manager reload"`
- [ ] Test connection: `telnet localhost 5038`

**1.3 Configure PJSIP Context**
- [ ] Create `/etc/asterisk/pjsip_kasaai.conf`:
```ini
; Include this file in pjsip.conf with: #include pjsip_kasaai.conf
; Virtual numbers for Kasa AI will be dynamically added here
```
- [ ] Edit `/etc/asterisk/pjsip.conf` to include: `#include pjsip_kasaai.conf`

**1.4 Configure Dialplan**
- [ ] Create `/etc/asterisk/extensions_kasaai.conf`:
```ini
[kasaai-virtual]
; Context for all virtual Kasa AI numbers
exten => _X.,1,NoOp(Incoming call to ${EXTEN})
    same => n,Set(WEBHOOK_URL=${DB(kasaai/webhook/${CALLERID(num)})})
    same => n,System(curl -X POST ${WEBHOOK_URL} \
        -H "Content-Type: application/json" \
        -d '{"from":"${CALLERID(num)}","to":"${EXTEN}","call_id":"${UNIQUEID}"}')
    same => n,Stasis(kasaai-call,${EXTEN})
    same => n,Hangup()
```
- [ ] Edit `/etc/asterisk/extensions.conf` to include: `#include extensions_kasaai.conf`

**1.5 Add Environment Variables**
- [ ] Add to `/opt/kasaai/.env`:
```bash
ASTERISK_AMI_HOST=127.0.0.1
ASTERISK_AMI_PORT=5038
ASTERISK_AMI_USER=kasaai
ASTERISK_AMI_SECRET=<the-secure-password-from-manager.conf>
ASTERISK_SERVER=asterisk.ailabsafrica.com
```

### Phase 2: Python Integration (Week 2)

**2.1 Install Dependencies**
- [ ] Add to `requirements.txt`:
```
panoramisk>=1.4
```
- [ ] Install: `/opt/kasaai/apps/venv/bin/pip install panoramisk`

**2.2 Create Asterisk Client Module**
- [ ] Create `/opt/kasaai/apps/core_backend/backend/services/asterisk_client.py`:

```python
"""
Asterisk AMI Client for Virtual Phone Number Management
"""
import os
import logging
from typing import Optional
from panoramisk import Manager
from ..models.phone_number import PhoneNumber

logger = logging.getLogger(__name__)

class AsteriskClient:
    """Client for managing Asterisk virtual phone numbers"""

    def __init__(self):
        self.host = os.getenv('ASTERISK_AMI_HOST', '127.0.0.1')
        self.port = int(os.getenv('ASTERISK_AMI_PORT', 5038))
        self.username = os.getenv('ASTERISK_AMI_USER', 'kasaai')
        self.secret = os.getenv('ASTERISK_AMI_SECRET')

        if not self.secret:
            raise ValueError("ASTERISK_AMI_SECRET not set in environment")

    async def connect(self) -> Manager:
        """Create and connect AMI manager"""
        manager = Manager(
            host=self.host,
            port=self.port,
            username=self.username,
            secret=self.secret
        )
        await manager.connect()
        return manager

    async def create_sip_peer(self, phone_number: PhoneNumber) -> bool:
        """
        Create SIP peer in Asterisk for virtual number

        Args:
            phone_number: PhoneNumber instance with SIP credentials

        Returns:
            bool: True if successful
        """
        try:
            manager = await self.connect()

            # Create PJSIP endpoint
            await self._create_pjsip_endpoint(manager, phone_number)

            # Create auth section
            await self._create_pjsip_auth(manager, phone_number)

            # Create AOR section
            await self._create_pjsip_aor(manager, phone_number)

            # Store webhook in AstDB
            await manager.command({
                'Action': 'DBPut',
                'Family': 'kasaai',
                'Key': f'webhook/{phone_number.number}',
                'Val': phone_number.webhook_url
            })

            # Reload PJSIP
            await manager.command({'Action': 'PJSIPReload'})

            await manager.close()

            logger.info(f"Created SIP peer for {phone_number.number}")
            return True

        except Exception as e:
            logger.error(f"Failed to create SIP peer: {e}")
            return False

    async def _create_pjsip_endpoint(self, manager: Manager, phone: PhoneNumber):
        """Create PJSIP endpoint section"""
        commands = {
            'Action': 'UpdateConfig',
            'SrcFilename': 'pjsip_kasaai.conf',
            'DstFilename': 'pjsip_kasaai.conf',
            'Action-000000': 'NewCat',
            'Cat-000000': phone.sip_username,
            'Action-000001': 'Append',
            'Cat-000001': phone.sip_username,
            'Var-000001': 'type',
            'Value-000001': 'endpoint',
            'Action-000002': 'Append',
            'Cat-000002': phone.sip_username,
            'Var-000002': 'context',
            'Value-000002': 'kasaai-virtual',
            'Action-000003': 'Append',
            'Cat-000003': phone.sip_username,
            'Var-000003': 'auth',
            'Value-000003': phone.sip_username,
            'Action-000004': 'Append',
            'Cat-000004': phone.sip_username,
            'Var-000004': 'aors',
            'Value-000004': phone.sip_username,
            'Action-000005': 'Append',
            'Cat-000005': phone.sip_username,
            'Var-000005': 'allow',
            'Value-000005': 'ulaw,alaw,gsm'
        }
        await manager.command(commands)

    async def _create_pjsip_auth(self, manager: Manager, phone: PhoneNumber):
        """Create PJSIP auth section"""
        commands = {
            'Action': 'UpdateConfig',
            'SrcFilename': 'pjsip_kasaai.conf',
            'DstFilename': 'pjsip_kasaai.conf',
            'Action-000000': 'NewCat',
            'Cat-000000': f'{phone.sip_username}-auth',
            'Action-000001': 'Append',
            'Cat-000001': f'{phone.sip_username}-auth',
            'Var-000001': 'type',
            'Value-000001': 'auth',
            'Action-000002': 'Append',
            'Cat-000002': f'{phone.sip_username}-auth',
            'Var-000002': 'auth_type',
            'Value-000002': 'userpass',
            'Action-000003': 'Append',
            'Cat-000003': f'{phone.sip_username}-auth',
            'Var-000003': 'username',
            'Value-000003': phone.sip_username,
            'Action-000004': 'Append',
            'Cat-000004': f'{phone.sip_username}-auth',
            'Var-000004': 'password',
            'Value-000004': phone.sip_password
        }
        await manager.command(commands)

    async def _create_pjsip_aor(self, manager: Manager, phone: PhoneNumber):
        """Create PJSIP AOR section"""
        commands = {
            'Action': 'UpdateConfig',
            'SrcFilename': 'pjsip_kasaai.conf',
            'DstFilename': 'pjsip_kasaai.conf',
            'Action-000000': 'NewCat',
            'Cat-000000': f'{phone.sip_username}-aor',
            'Action-000001': 'Append',
            'Cat-000001': f'{phone.sip_username}-aor',
            'Var-000001': 'type',
            'Value-000001': 'aor',
            'Action-000002': 'Append',
            'Cat-000002': f'{phone.sip_username}-aor',
            'Var-000002': 'max_contacts',
            'Value-000002': '1'
        }
        await manager.command(commands)

    async def delete_sip_peer(self, phone_number: PhoneNumber) -> bool:
        """
        Delete SIP peer from Asterisk

        Args:
            phone_number: PhoneNumber instance to remove

        Returns:
            bool: True if successful
        """
        try:
            manager = await self.connect()

            # Remove from config
            await manager.command({
                'Action': 'UpdateConfig',
                'SrcFilename': 'pjsip_kasaai.conf',
                'DstFilename': 'pjsip_kasaai.conf',
                'Action-000000': 'DelCat',
                'Cat-000000': phone_number.sip_username
            })

            # Remove webhook from AstDB
            await manager.command({
                'Action': 'DBDel',
                'Family': 'kasaai',
                'Key': f'webhook/{phone_number.number}'
            })

            # Reload PJSIP
            await manager.command({'Action': 'PJSIPReload'})

            await manager.close()

            logger.info(f"Deleted SIP peer for {phone_number.number}")
            return True

        except Exception as e:
            logger.error(f"Failed to delete SIP peer: {e}")
            return False

    async def test_connection(self) -> bool:
        """Test AMI connection"""
        try:
            manager = await self.connect()
            await manager.close()
            return True
        except Exception as e:
            logger.error(f"AMI connection test failed: {e}")
            return False
```

**2.3 Update Phone Numbers Route**
- [ ] Modify `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/phone_numbers.py`:

```python
from ...services.asterisk_client import AsteriskClient

class PhoneNumbersAPI:
    def __init__(self):
        # ... existing code ...
        self.asterisk_client = AsteriskClient()

    async def _register_with_asterisk(self, phone_number: PhoneNumber):
        """Register virtual number with Asterisk"""
        try:
            success = await self.asterisk_client.create_sip_peer(phone_number)
            if not success:
                raise Exception("Failed to register with Asterisk")
            return True
        except Exception as e:
            logger.error(f"Asterisk registration failed for {phone_number.number}: {e}")
            raise

    async def _unregister_from_asterisk(self, phone_number: PhoneNumber):
        """Unregister virtual number from Asterisk"""
        try:
            success = await self.asterisk_client.delete_sip_peer(phone_number)
            if not success:
                logger.warning(f"Failed to unregister {phone_number.number} from Asterisk")
            return True
        except Exception as e:
            logger.error(f"Asterisk unregistration failed: {e}")
            return False
```

### Phase 3: Call Webhook Handler (Week 2)

**3.1 Create Webhook Endpoint**
- [ ] Create `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/call_webhook.py`:

```python
"""
Call webhook handler for Asterisk incoming calls
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

class IncomingCall(BaseModel):
    """Incoming call from Asterisk"""
    from_number: str
    to_number: str
    call_id: str

@router.post("/voice/webhook/{sip_username}")
async def handle_incoming_call(sip_username: str, call: IncomingCall):
    """
    Handle incoming call from Asterisk

    This endpoint is called by Asterisk dialplan when a call comes in
    to a virtual Kasa AI number. It should route the call to the assigned
    voice assistant using FastRTC or Vapi.
    """
    logger.info(f"Incoming call to {sip_username}: {call.from_number} -> {call.to_number}")

    # TODO: Integrate with FastRTC/Vapi
    # 1. Look up assigned assistant for this phone number
    # 2. Create voice session
    # 3. Bridge call to assistant

    return {
        "status": "success",
        "message": "Call routed to assistant",
        "call_id": call.call_id
    }
```

- [ ] Register router in main app

### Phase 4: Testing (Week 3)

**4.1 Unit Tests**
- [ ] Create `/opt/kasaai/apps/core_backend/tests/test_asterisk_client.py`:

```python
import pytest
from backend.services.asterisk_client import AsteriskClient
from backend.models.phone_number import PhoneNumber, PhoneProvider, PhoneNumberType, PhoneNumberStatus

@pytest.mark.asyncio
async def test_asterisk_connection():
    """Test AMI connection"""
    client = AsteriskClient()
    assert await client.test_connection()

@pytest.mark.asyncio
async def test_create_sip_peer():
    """Test SIP peer creation"""
    client = AsteriskClient()

    phone = PhoneNumber(
        id="test_123",
        number="+1234567890",
        provider=PhoneProvider.KASAAI,
        type=PhoneNumberType.BOTH,
        status=PhoneNumberStatus.PENDING,
        country="United States",
        country_code="+1",
        capabilities=["voice"],
        monthly_cost=1.00,
        setup_cost=0.00,
        sip_username="test_kasaai_123",
        sip_password="secure_password_123",
        sip_server="asterisk.ailabsafrica.com",
        webhook_url="https://api.kasaai.ailabsafrica.com/voice/webhook/test_kasaai_123"
    )

    # Create peer
    success = await client.create_sip_peer(phone)
    assert success

    # Clean up
    await client.delete_sip_peer(phone)
```

**4.2 Integration Tests**
- [ ] Test full provisioning flow with real Asterisk server
- [ ] Test SIP registration with softphone (Zoiper, Linphone)
- [ ] Test incoming call routing to webhook

**4.3 Load Tests**
- [ ] Provision 100 virtual numbers
- [ ] Verify all registered in Asterisk
- [ ] Test concurrent call handling

### Phase 5: Production Deployment (Week 4)

**5.1 Production Server Setup**
- [ ] Deploy Asterisk configuration to production (148.251.0.46)
- [ ] Configure firewall for SIP traffic (UDP 5060, RTP 10000-20000)
- [ ] Set up monitoring and logging

**5.2 Code Deployment**
- [ ] Deploy new backend code
- [ ] Restart kasaai-core-backend service
- [ ] Verify webhook endpoint accessible

**5.3 Monitoring**
- [ ] Set up Asterisk log monitoring
- [ ] Add metrics for call volume
- [ ] Alert on registration failures

---

## 5. Technical Considerations

### Security

1. **AMI Access**
   - Bind to localhost only (127.0.0.1)
   - Use strong password (32+ chars)
   - Rotate credentials regularly

2. **SIP Security**
   - Generate strong SIP passwords (16+ chars)
   - Use encryption (SRTP) if possible
   - Rate limit registration attempts

3. **Webhook Security**
   - Validate call_id matches Asterisk format
   - Add HMAC signature verification
   - Rate limit webhook calls

### Scalability

1. **Connection Pooling**
   - Reuse AMI connections where possible
   - Implement connection pool for high concurrency

2. **Async Operations**
   - All Asterisk operations are async
   - Non-blocking call handling

3. **Database**
   - Consider moving phone_numbers from in-memory to MongoDB
   - Add indexing on number, sip_username

### Error Handling

1. **Asterisk Unavailable**
   - Retry logic with exponential backoff
   - Queue operations for retry
   - Alert operations team

2. **Configuration Errors**
   - Validate configuration before applying
   - Rollback on failure
   - Keep backup of working config

3. **Call Routing Failures**
   - Log detailed error info
   - Return busy signal to caller
   - Alert on high failure rate

---

## 6. Alternative: Simplified Approach (If Asterisk Not Available)

If we don't have Asterisk available or installation is blocked, we can use a **SIP Provider Proxy** approach:

1. Use Twilio/Vonage for actual numbers
2. Register our backend as a SIP endpoint with them
3. Handle incoming calls via their webhooks
4. Present it as "Kasa AI numbers" in the UI
5. Keep the pricing tiers but internally use provider's API

This would require minimal backend changes but wouldn't give us full control.

---

## 7. Success Criteria

✅ **Phase 1 Complete When:**
- Asterisk installed and running
- AMI enabled and accessible
- Dialplan configured and loaded
- Environment variables set

✅ **Phase 2 Complete When:**
- Python AMI client working
- Can create/delete SIP peers programmatically
- Unit tests passing

✅ **Phase 3 Complete When:**
- Webhook endpoint receiving calls
- Can route calls to voice assistants
- Integration tests passing

✅ **Phase 4 Complete When:**
- All tests passing
- Can provision 100+ numbers without errors
- SIP registration working with real clients

✅ **Phase 5 Complete When:**
- Production deployment successful
- Monitoring and alerts active
- First customer call handled successfully

---

## 8. Estimated Timeline

- **Week 1**: Infrastructure setup (Asterisk installation, configuration)
- **Week 2**: Python integration (AMI client, route updates, webhook)
- **Week 3**: Testing (unit, integration, load tests)
- **Week 4**: Production deployment and monitoring

**Total: 4 weeks** for full integration

**MVP (Minimum Viable Product): 2 weeks** - Basic provisioning and SIP registration working

---

## 9. Resources Required

1. **Server Access**
   - SSH/sudo access to production server (148.251.0.46)
   - Ability to install packages (apt install asterisk)
   - Firewall rule changes for SIP traffic

2. **Testing**
   - SIP softphone for testing (Zoiper, Linphone)
   - Test phone numbers for incoming call tests
   - Dev server (85.214.12.174) for staging

3. **Documentation**
   - Asterisk AMI documentation: https://wiki.asterisk.org/wiki/display/AST/AMI
   - PJSIP configuration: https://wiki.asterisk.org/wiki/display/AST/PJSIP+Configuration+Wizard
   - panoramisk library: https://github.com/gawel/panoramisk

---

## 10. Next Steps

**Immediate Actions:**

1. ✅ **Decision Point**: Do we have Asterisk available on our servers?
   - [ ] Check if installed: SSH and run `asterisk -V`
   - [ ] If not, decide: Install Asterisk OR use simplified SIP provider proxy approach

2. ✅ **If Asterisk Available**: Proceed with Phase 1
   - [ ] Configure AMI
   - [ ] Set up dialplan
   - [ ] Test connection

3. ✅ **If Not Available**: Design simplified approach
   - [ ] Document SIP provider proxy architecture
   - [ ] Estimate effort for proxy implementation
   - [ ] Compare costs vs full Asterisk

4. ✅ **Get Approval**: Present this plan to stakeholders
   - [ ] Review timeline and resources
   - [ ] Approve budget for infrastructure
   - [ ] Assign development resources

**Questions to Answer:**

1. Do we already have Asterisk running on 148.251.0.46?
2. Can we install new services on the production server?
3. What's the budget/timeline for this feature?
4. Do we need to support international calls immediately?
5. What level of call quality/reliability is acceptable for MVP?

---

## Appendix A: Asterisk Installation Commands

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Asterisk and modules
sudo apt install -y asterisk asterisk-modules asterisk-core-sounds-en-gsm

# Enable and start service
sudo systemctl enable asterisk
sudo systemctl start asterisk

# Verify installation
asterisk -V
sudo systemctl status asterisk

# Test CLI access
sudo asterisk -rx "core show version"
```

## Appendix B: Environment Variables

Add to `/opt/kasaai/.env`:

```bash
# Asterisk AMI Configuration
ASTERISK_AMI_HOST=127.0.0.1
ASTERISK_AMI_PORT=5038
ASTERISK_AMI_USER=kasaai
ASTERISK_AMI_SECRET=<generate-with-openssl-rand-base64-32>

# Asterisk Server
ASTERISK_SERVER=asterisk.ailabsafrica.com
ASTERISK_SIP_PORT=5060

# Call Webhook
CALL_WEBHOOK_BASE_URL=https://api.kasaai.ailabsafrica.com/voice/webhook
```

## Appendix C: Testing Checklist

- [ ] AMI connection test
- [ ] SIP peer creation test
- [ ] SIP peer deletion test
- [ ] Dialplan execution test
- [ ] Webhook invocation test
- [ ] Call routing to assistant test
- [ ] Multiple concurrent calls test
- [ ] Number provisioning end-to-end test
- [ ] Number deletion cleanup test
- [ ] Error handling tests (Asterisk down, invalid config, etc.)

---

**Document Version:** 1.0
**Created:** 2025-11-12
**Author:** Claude (AI Labs Africa Development Team)
**Status:** Pending Review & Approval
