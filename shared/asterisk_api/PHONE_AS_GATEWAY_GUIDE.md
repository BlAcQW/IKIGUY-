# Using Your Phone as a SIP Gateway

## Overview

You can use your Android/iPhone with a SIM card as a gateway to test phone number routing. This is perfect for development and testing before investing in dedicated hardware.

## 🎯 What You'll Achieve

```
Your Phone (with SIM) → SIP → Asterisk → Webhook → Vapi → AI Assistant
```

When someone calls your real phone number, it will:
1. Register as a SIP endpoint with Asterisk
2. Forward the call to your webhook
3. Route to your Vapi assistant
4. The AI assistant answers!

## 📱 Method 1: Simple SIP Client (Recommended for Testing)

### Step 1: Install a SIP Client App

**For Android:**
- **Linphone** (Free, Open Source) - Recommended
- **Zoiper** (Free tier available)
- **GSWave** (Free)

**For iPhone:**
- **Linphone** (Free)
- **Zoiper** (Free tier)
- **Groundwire** ($9.99 - best quality)

### Step 2: Configure Your SIP Account

Use the credentials from your provisioned number:

```
Number: +2330247535969
SIP Username: kasaai_20251112133610
SIP Password: t4F8giscgWzhKlsF
SIP Server: asterisk.ailabsafrica.com
Port: 5060
Transport: UDP (or TCP)
```

### Step 3: Linphone Configuration (Example)

1. **Open Linphone** → Tap "Use SIP Account"
2. **Username**: `kasaai_20251112133610`
3. **Password**: `t4F8giscgWzhKlsF`
4. **Domain**: `asterisk.ailabsafrica.com`
5. **Transport**: UDP
6. **Advanced Settings**:
   - Enable "Push notifications" (for incoming calls)
   - Enable "Keep alive" (stay registered)
   - Set "Expire": 3600

### Step 4: Verify Registration

Check if your phone registered:

```bash
curl -s https://asterisk-api.ailabsafrica.com/sip/peers
```

You should see `kasaai_20251112133610` in the list!

## 📞 Method 2: Call Forwarding (Easiest - No SIP)

If you just want to test, use your carrier's call forwarding:

### Option A: Android Built-in
```
Settings → Call Settings → Call Forwarding
Forward to: [Vapi test number or Twilio number]
```

### Option B: USSD Code (Ghana MTN)
```
Dial: *21*[forward-number]#
To cancel: ##21#
```

This forwards YOUR number to any destination!

## 🔧 Method 3: Advanced - Phone as Full Gateway

For more control, turn your phone into a full GSM gateway:

### Requirements:
- Android phone (rooted preferred)
- SIM card
- "GSM Gateway" app or similar

### Apps for Android:
1. **GOIP Simulator** - Turns Android into GoIP-compatible gateway
2. **SIP2SIM** - Routes SIP calls to GSM network
3. **GSM Gateway for Android** - Commercial solution

### Setup Process:
1. Install GSM Gateway app
2. Configure SIP server (asterisk.ailabsafrica.com)
3. Set routing rules (SIP → GSM)
4. Keep phone plugged in and connected to WiFi

## 🎯 Testing Your Setup

### Test 1: Verify SIP Registration
```bash
# Check if phone is registered
curl https://asterisk-api.ailabsafrica.com/sip/peer/kasaai_20251112133610
```

### Test 2: Make Test Call
From Linphone on your phone:
```
Call: echo@asterisk.ailabsafrica.com
# Should hear echo test
```

### Test 3: Incoming Call Webhook
```bash
# Test webhook endpoint
curl -X POST https://api.kasaai.ailabsafrica.com/voice/webhook/kasaai_20251112133610 \
  -H "Content-Type: application/json" \
  -d '{
    "event": "call.started",
    "from": "+233501234567",
    "to": "+2330247535969"
  }'
```

## 🔥 Quick Start for YOUR Number (+2330247535969)

### Option 1: Install Linphone NOW (5 minutes)

1. **Download Linphone** from App Store/Play Store

2. **Add Account** with these exact details:
   ```
   Username: kasaai_20251112133610
   Password: t4F8giscgWzhKlsF
   Server: asterisk.ailabsafrica.com
   ```

3. **Wait for "Registered" status** (green dot)

4. **Test by calling**: `echo@asterisk.ailabsafrica.com`

5. **Now you can receive calls** on +2330247535969!

### Option 2: Use Vapi's Phone Number (Instant)

If you just want to test the assistant:

1. Go to [Vapi Dashboard](https://vapi.ai)
2. Find your assistant (Agric Dev Bank)
3. Click "Get Phone Number"
4. Vapi provisions a real DID instantly
5. Call it to test!

## 📊 Comparison

| Method | Setup Time | Cost | Reliability | Use Case |
|--------|-----------|------|-------------|----------|
| **Linphone SIP** | 5 min | Free | Medium | Development testing |
| **Call Forwarding** | 1 min | Carrier rates | High | Quick testing |
| **GSM Gateway App** | 30 min | $0-50 | Medium | Advanced testing |
| **Vapi Numbers** | Instant | $0.013/min | High | Production |
| **Twilio Import** | 10 min | $1/mo + usage | Very High | Production |
| **Hardware Gateway** | Hours | $100-500 | Very High | Production |

## 🚨 Important Notes

### For Production:
- **Don't use your personal phone** - battery drain, unreliable
- **Use dedicated gateway** (GoIP, Grandstream)
- **Or use cloud providers** (Twilio, Vonage)

### For Testing:
- ✅ **Linphone/Zoiper** is perfect!
- ✅ Keep phone plugged in
- ✅ Keep app running in background
- ✅ Stable WiFi connection

### Network Considerations:
- **WiFi required** for SIP registration
- **Mobile data** works but uses data for calls
- **Firewall** - ensure ports 5060 (SIP) and 10000-20000 (RTP) open
- **NAT** - may need STUN server configuration

## 🎯 Next Steps

1. **Install Linphone** right now
2. **Register using your credentials** above
3. **Test with echo service**
4. **Check Dashboard** - you'll see it in Phone Routes tab
5. **Make a test call** to +2330247535969

## 🔧 Troubleshooting

### "Registration Failed"
```bash
# Check Asterisk API is reachable
curl https://asterisk-api.ailabsafrica.com/health

# Re-register SIP peer
curl -X POST https://asterisk-api.ailabsafrica.com/sip/peer \
  -H "Content-Type: application/json" \
  -d '{
    "number": "+2330247535969",
    "sip_username": "kasaai_20251112133610",
    "sip_password": "t4F8giscgWzhKlsF",
    "webhook_url": "https://api.kasaai.ailabsafrica.com/voice/webhook/kasaai_20251112133610",
    "context": "kasaai-virtual"
  }'
```

### "Can't Make/Receive Calls"
- Check firewall allows UDP port 5060
- Enable "Keep alive" in Linphone settings
- Try TCP transport instead of UDP
- Check battery optimization doesn't kill app

### "No Audio"
- Check RTP ports (10000-20000) not blocked
- Enable "Media encryption" in app settings
- Try different codec (PCMU/PCMA)

## 📱 Recommended Apps

### Free & Reliable:
1. **Linphone** - Best for development
2. **Zoiper Free** - Simple interface

### Premium:
1. **Groundwire** (iOS) - Professional quality
2. **Zoiper Premium** - Advanced features

## 💡 Pro Tips

1. **Battery Life**: Keep phone plugged in when testing
2. **Notifications**: Enable push notifications for incoming calls
3. **Network**: Use WiFi for stable connection
4. **Testing**: Use echo service to test audio quality
5. **Monitoring**: Check Phone Routes tab in dashboard to see registration status

---

**Ready to test?** Install Linphone now and use the credentials from your provisioned number!
