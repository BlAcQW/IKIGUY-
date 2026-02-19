# VAPI Inbound Call Troubleshooting Guide

## Issue
Outbound calls work ✅, but inbound calls fail with "can't find number" ❌

## Root Cause - CRITICAL FINDING ⚠️

**VAPI does NOT support SIP REGISTER (registration-based authentication)**

After extensive testing and documentation review, VAPI's BYOT (Bring Your Own Trunk) feature does NOT support acting as a SIP client that registers to your provider's server using SIP REGISTER messages.

### What VAPI Supports:
- ✅ **Outbound calls**: VAPI initiates calls and authenticates with username/password
- ✅ **IP/Domain-based inbound routing**: Provider routes calls directly to VAPI's SIP domain WITHOUT registration

### What VAPI Does NOT Support:
- ❌ **SIP REGISTER**: VAPI cannot send REGISTER messages to your provider's server
- ❌ **Registration-based inbound**: VAPI cannot "register" with your provider to receive inbound calls

### The Problem:
Ant Cellular's VitalPBX system uses registration-based routing. When you call +233308249843, VitalPBX checks its registration table to find where the number is registered. Since VAPI doesn't register with VitalPBX, it says "can't find number".

---

## Possible Solutions

### Solution 1: Ask Ant Cellular to Configure IP/Domain-Based Routing (Recommended)

Request Ant Cellular to configure **static/IP-based inbound routing** instead of registration-based routing.

**What to ask Ant Cellular:**
"Can you configure static inbound routing for +233308249843 to forward calls to our SIP domain without requiring SIP REGISTER?"

**Configuration they need to add:**
```
DID/Number: +233308249843 (or 0308249843)
Route Type: Static SIP Route (not registration-based)
Destination: 92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai:5060
SIP URI: +233308249843@92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai
```

**Benefits:**
- ✅ Works with VAPI's architecture
- ✅ No registration required
- ✅ Reliable routing

### Solution 2: Use a SIP Proxy/Gateway - ✅ IMPLEMENTED

We have implemented an Asterisk SIP proxy that:
1. Registers with Ant Cellular (acts as SIP client)
2. Routes calls to VAPI (acts as SIP server)

**Implementation Details:**
- **Location**: `/opt/kasaai/asterisk/`
- **Container**: `kasaai-asterisk-proxy`
- **IP**: `148.251.0.46:5060`
- **Documentation**: See `/opt/kasaai/asterisk/ASTERISK_SETUP.md`

**Current Status:**
- ✅ Asterisk proxy running and configured
- ✅ VAPI updated to route through Asterisk (gateway: 148.251.0.46)
- ❌ Registration with Ant Cellular: **Rejected** (IP not whitelisted)

**What's Needed:**
- Ask Ant Cellular to whitelist IP `148.251.0.46` for SIP registration
- OR ask Ant Cellular to configure static DID routing for +233308249843 to `148.251.0.46:5060`

**Advantages:**
- ✅ Bridges incompatibility between VAPI and Ant Cellular
- ✅ Works with registration-based providers
- ✅ Can be managed locally on our server

**Disadvantages:**
- ❌ Requires maintaining additional infrastructure
- ❌ Additional point of failure (but can be monitored)
- ❌ Still requires Ant Cellular to whitelist our IP or configure static routing

### Solution 3: Use Ant Cellular for Outbound Only + Different Provider for Inbound

Use VAPI's built-in phone number providers (Twilio, Vonage, etc.) for inbound calls, and keep Ant Cellular for outbound only.

**Benefits:**
- ✅ Simple setup
- ✅ VAPI handles everything

**Drawbacks:**
- ❌ Can't use +233308249843 for inbound
- ❌ Need different number for inbound calls

---

## VAPI Configuration (Verified ✅)

### Phone Number
- **Number**: +233308249843
- **Phone Number ID**: 6d828206-4eba-4668-9bb1-8c2f8045b682
- **Provider**: byo-phone-number
- **Status**: Active ✅
- **Assistant ID**: cde22a1e-1247-42bb-8c15-1df608c28798 ✅

### SIP Trunk Credential
- **Credential ID**: 92d72cfd-e4af-4117-b260-c11c13d376fe
- **Name**: ant cellular trunk
- **Provider**: byo-sip-trunk
- **Gateway**: vitalpbx.antcellular.com:5060
- **Auth Username**: 308249843
- **Auth Password**: Hyhhzn3RdMwVMB7c4cw2 (configured, not visible in API)
- **Outbound**: Enabled ✅
- **Inbound**: Enabled ✅
- **Status**: Active ✅

**Note:** Credentials updated with Ant Cellular VitalPBX authentication details, but VAPI still cannot REGISTER to their server.

---

## Required Ant Cellular Configuration

### 🔧 Inbound Call Routing Setup

Contact Ant Cellular support and request them to configure **inbound call routing** for **+233308249843** to forward to VAPI's SIP domain.

### Configuration Details to Provide to Ant Cellular:

#### Option 1: Full E.164 Format (Recommended)
```
SIP URI: +233308249843@92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai
Host/Domain: 92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai
Port: 5060 (or 5061 for TLS)
Transport: UDP or TCP
```

#### Option 2: Local Number Format (Alternative)
```
SIP URI: 0308249843@92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai
Host/Domain: 92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai
User/Extension: 0308249843
Port: 5060 (or 5061 for TLS)
```

#### Option 3: IP-Based Routing
```
SIP Destination: sip:+233308249843@92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai:5060
```

---

## Troubleshooting Steps

### Step 1: Verify Ant Cellular Configuration
Contact Ant Cellular and verify:
- [ ] Is inbound routing/call forwarding configured for +233308249843?
- [ ] What SIP URI are they currently forwarding to?
- [ ] Are there any error logs showing failed routing attempts?
- [ ] Is the SIP domain whitelisted: `92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai`?

### Step 2: Check SIP Trunk Settings
```bash
# Verify VAPI SIP trunk credential
curl -X GET "https://api.vapi.ai/credential/92d72cfd-e4af-4117-b260-c11c13d376fe" \
  -H "Authorization: Bearer 42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
```

Expected:
- ✅ Gateway IP: 139.84.239.136
- ✅ Auth Username: 0308249843
- ✅ Status: active

### Step 3: Test Inbound Call
1. Call +233308249843 from an external phone
2. Expected behavior:
   - Ant Cellular receives the call
   - Routes it to `92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai`
   - VAPI answers with assistant `cde22a1e-1247-42bb-8c15-1df608c28798`

3. If it fails, check error message:
   - "Can't find number" → Ant Cellular not routing to VAPI
   - "Authentication failed" → Check SIP credentials
   - "Timeout" → Check network/firewall

### Step 4: Monitor VAPI Logs
Check VAPI dashboard or use API to monitor incoming calls:
```bash
# List recent calls
curl -X GET "https://api.vapi.ai/call?phoneNumberId=6d828206-4eba-4668-9bb1-8c2f8045b682" \
  -H "Authorization: Bearer 42cf1e7c-2ef9-4bd7-ba30-52f2813605a2"
```

---

## Common Issues and Solutions

### Issue 1: "Can't find number"
**Cause**: Ant Cellular is not routing inbound calls to VAPI
**Solution**: Configure inbound routing at Ant Cellular (see configuration above)

### Issue 2: "No route to destination"
**Cause**: Wrong SIP domain or DNS issue
**Solution**:
- Verify SIP domain: `92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai`
- Test DNS resolution: `nslookup 92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai`

### Issue 3: "Authentication failed"
**Cause**: Wrong SIP credentials
**Solution**:
- Verify auth username: `0308249843`
- VAPI handles authentication, no password needed from Ant Cellular

### Issue 4: Call connects but no audio
**Cause**: Media/RTP routing issue
**Solution**:
- Check firewall allows RTP ports (typically 10000-20000 UDP)
- Verify NAT traversal settings

---

## Technical Details

### How Inbound Calls Should Work:
1. **External caller** dials +233308249843
2. **Ant Cellular** receives the call on their network
3. **Ant Cellular** routes the call via SIP to:
   `+233308249843@92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai`
4. **VAPI** receives the SIP INVITE
5. **VAPI** looks up phone number `+233308249843` (ID: 6d828206-4eba-4668-9bb1-8c2f8045b682)
6. **VAPI** connects the call to assistant `cde22a1e-1247-42bb-8c15-1df608c28798`
7. **Assistant** answers and starts conversation

### Current Status:
- ✅ Steps 4-7 are configured correctly in VAPI
- ❌ Steps 2-3 need to be configured at Ant Cellular

---

## Testing Commands

### Test Outbound Call (Working ✅)
```bash
curl -X POST "https://api.vapi.ai/call/phone" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer 42cf1e7c-2ef9-4bd7-ba30-52f2813605a2" \
  -d '{
    "assistantId": "cde22a1e-1247-42bb-8c15-1df608c28798",
    "customer": {
      "number": "+233XXXXXXXXX",
      "numberE164CheckEnabled": false
    },
    "phoneNumberId": "6d828206-4eba-4668-9bb1-8c2f8045b682"
  }'
```

### Check DNS Resolution
```bash
nslookup 92d72cfd-e4af-4117-b260-c11c13d376fe.sip.vapi.ai
```

Expected output should show valid IP addresses.

---

## Next Steps

### Current Implementation Status (2025-11-12) ✅

We have implemented **Solution 2 (Asterisk SIP Proxy)** at `148.251.0.46:5060`.

**What's Working:**
- ✅ Asterisk proxy running and healthy
- ✅ VAPI configured to route through Asterisk (gateway: 148.251.0.46:5060)
- ✅ **Successfully registered with Ant Cellular VitalPBX**
  - Extension: 308249843
  - Server: vitalpbx.antcellular.com
  - IP whitelisted: 148.251.0.46
  - Status: **Registered** (auto-renews every hour)
- ✅ Dialplan configured for bidirectional call routing

**What's Pending:**
- ⏳ **Ant Cellular DID Routing Configuration Needed**
  - Inbound calls to +233308249843 need to be routed to extension 308249843
  - Currently, calls go to voicemail instead of our registered proxy
  - See `/opt/kasaai/asterisk/MESSAGE_TO_ANT_CELLULAR.md` for detailed configuration request

**Next Actions:**

1. **Contact Ant Cellular** (Eyome) - **Copy from `/opt/kasaai/asterisk/SHORT_MESSAGE_TO_EYOME.txt`**

Request them to configure VitalPBX inbound routing:

```
Hi Eyome,

Good news! Our system has successfully registered with your VitalPBX server as extension 308249843 from IP 148.251.0.46.

However, when we test calling +233308249843, the calls don't reach us - they go to voicemail instead.

Could you please configure VitalPBX to route inbound calls to +233308249843 to extension 308249843?

In VitalPBX, this should be:
PBX → Inbound Routes → Create New Route
- DID Number: +233308249843 (or 0308249843 or 308249843)
- Destination: Extension 308249843

Once configured, please let us know so we can test again.

Thank you!
```

See `/opt/kasaai/asterisk/MESSAGE_TO_ANT_CELLULAR.md` for detailed technical documentation.

2. **After Ant Cellular Configures DID Routing:**
   - Test inbound call by calling +233308249843
   - Verify call reaches our Asterisk proxy
   - Verify call forwards to VAPI assistant

3. **Testing:**
   - Call +233308249843 from external phone
   - Monitor Asterisk: `docker logs -f kasaai-asterisk-proxy`
   - Check registration: `docker exec kasaai-asterisk-proxy asterisk -rx "pjsip show registrations"`

4. **Monitoring:**
   - See `/opt/kasaai/asterisk/ASTERISK_SETUP.md` for management commands

---

## Contact Information

- **Ant Cellular Support**: Contact them to configure inbound routing
- **VAPI Support**: support@vapi.ai (if issues persist after Ant Cellular setup)

---

## Summary

**Root Cause**: Ant Cellular needs to configure inbound call forwarding/routing to VAPI's SIP domain.

**VAPI Side**: ✅ Fully configured and ready
**Ant Cellular Side**: ❌ Needs inbound routing configuration

**Action Required**: Contact Ant Cellular and provide them with the SIP URI configuration above.
