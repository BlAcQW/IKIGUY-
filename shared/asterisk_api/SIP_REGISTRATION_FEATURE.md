# SIP Registration with QR Code Feature

## 🎉 Feature Complete!

The SIP Registration feature with QR code scanning is now live in the Telephony dashboard.

## 📍 Access

Go to: **https://kasaai.ailabsafrica.com/telephony**
- Click the **"SIP Setup"** tab (first tab, opens by default)

## ✨ Features Implemented

### 1. **QR Code Generation**
- Select your provisioned phone number
- Click "Generate QR Code"
- Instantly get a Linphone-compatible QR code

### 2. **Auto-Configuration**
The QR code contains a `linphone-config://` URI that includes:
- SIP username
- SIP password
- Domain (asterisk.ailabsafrica.com)
- Transport (UDP)
- Display name

### 3. **Real-Time Registration Status**
- Automatically checks every 5 seconds
- Shows:
  - ✅ Registered / ❌ Not Registered
  - IP address (when registered)
  - User agent (device info)
  - Last registration time

### 4. **ANT Cellular Gateway Status**
- Shows status of ANT hardware gateways
- SIM registration status
- Network provider info
- Signal strength
- Currently shows "offline" (no hardware connected)

## 🚀 How to Use

### Step 1: Access the Dashboard
```
https://kasaai.ailabsafrica.com/telephony
→ Click "SIP Setup" tab
```

### Step 2: Select Your Number
Your provisioned number **+2330247535969** should appear in the list.
Click on it to select.

### Step 3: Generate QR Code
Click the "Generate QR Code" button.
A QR code will appear instantly.

### Step 4: Scan with Linphone
1. **Download Linphone** app (if not already installed)
   - Android: [Play Store](https://play.google.com/store/apps/details?id=org.linphone)
   - iPhone: [App Store](https://apps.apple.com/app/linphone/id360065638)

2. **Open Linphone** → Tap menu (≡) → **"Scan QR Code"**

3. **Scan the QR code** from your screen

4. **Linphone auto-configures** the account!

### Step 5: Watch Registration Status
The dashboard will automatically update to show:
```
✅ Registered
IP: [Your phone's IP]
Device: Linphone/[version]
```

## 🎯 What Happens When You Call Your Number

```
Caller dials +2330247535969
         ↓
Your Phone (Linphone) receives call
         ↓
Phone forwards via SIP to Asterisk
         ↓
Asterisk triggers webhook
         ↓
Backend routes to assigned assistant
         ↓
Vapi AI Assistant answers!
```

## 📱 Your Credentials

For manual setup (if QR doesn't work):

```
Username: kasaai_20251112133610
Password: t4F8giscgWzhKlsF
Domain: asterisk.ailabsafrica.com
Port: 5060
Transport: UDP
```

## 🔧 API Endpoints

### Generate QR Code
```bash
POST https://api.ailabsafrica.com/sip-registration/generate-qr
Content-Type: application/json

{
  "phone_number": "+2330247535969",
  "sip_username": "kasaai_20251112133610",
  "sip_password": "t4F8giscgWzhKlsF",
  "display_name": "My Phone"
}

Response:
{
  "qr_code_data_url": "data:image/png;base64,...",
  "sip_uri": "sip:kasaai_20251112133610@asterisk.ailabsafrica.com",
  "linphone_uri": "linphone-config:username=...",
  "credentials": {...},
  "instructions": "..."
}
```

### Check Registration Status
```bash
GET https://api.ailabsafrica.com/sip-registration/status/kasaai_20251112133610

Response:
{
  "success": true,
  "sip_username": "kasaai_20251112133610",
  "status": "registered",
  "registered": true,
  "ip_address": "192.168.1.100",
  "user_agent": "Linphone/5.2.0",
  "last_registration": "2025-11-12T14:30:00Z"
}
```

### ANT Cellular Status
```bash
GET https://api.ailabsafrica.com/sip-registration/ant-cellular/status

Response:
{
  "success": true,
  "gateways": [...],
  "total_gateways": 1,
  "online_gateways": 0,
  "message": "No ANT cellular gateways detected."
}
```

## 📊 Dashboard Components

### 1. **SIPRegistrationPanel** (Main Component)
- Location: `/opt/kasaai/apps/b2c-portal/src/components/telephony/SIPRegistrationPanel.tsx`
- Features:
  - Phone number selection
  - QR code generation
  - Real-time status monitoring
  - ANT gateway status

### 2. **Backend Routes**
- Location: `/opt/kasaai/apps/core_backend/backend/routes/voice_engine/sip_registration.py`
- Endpoints:
  - `POST /sip-registration/generate-qr`
  - `GET /sip-registration/status/{sip_username}`
  - `GET /sip-registration/ant-cellular/status`

### 3. **QR Code Service**
- Location: `/opt/kasaai/apps/shared/services/qr_service.py`
- Used for generating high-quality QR codes
- Supports branding, logos, custom colors

## 🎨 UI Screenshots

### SIP Setup Tab
```
┌─────────────────────────────────────────────────────┐
│ Telephony Infrastructure                            │
├─────────────────────────────────────────────────────┤
│ [SIP Setup] [Metrics] [Alerts] [Phone Routes] ...  │
├─────────────────────────────────────────────────────┤
│                                                      │
│ ┌─ ANT Cellular Gateway Status ─────────────────┐  │
│ │ ⚠️ No ANT cellular gateways detected           │  │
│ │ Use Linphone SIP registration instead         │  │
│ └───────────────────────────────────────────────┘  │
│                                                      │
│ ┌─ SIP Registration - Use Your Phone ───────────┐  │
│ │                                                │  │
│ │ Select Phone Number:                           │  │
│ │ ☑ +2330247535969 [Assigned]                   │  │
│ │                                                │  │
│ │ [Generate QR Code]                             │  │
│ │                                                │  │
│ │ ┌────────────────┐                            │  │
│ │ │   QR CODE      │  Scan with Linphone App    │  │
│ │ │   IMAGE HERE   │  Open → Menu → Scan QR     │  │
│ │ └────────────────┘                            │  │
│ │                                                │  │
│ │ ┌─ Registration Status ─────────────────────┐ │  │
│ │ │ ✅ Registered                              │ │  │
│ │ │ IP: 192.168.1.100                         │ │  │
│ │ │ Device: Linphone/5.2.0                    │ │  │
│ │ └───────────────────────────────────────────┘ │  │
│ └───────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

## ✅ Testing Checklist

- [x] Backend endpoints created
- [x] Frontend component built
- [x] QR code generation working
- [x] Registration status monitoring
- [x] ANT cellular status display
- [x] Frontend deployed
- [x] Backend restarted
- [x] API endpoints tested

## 🔜 Next Steps

1. **Download Linphone** on your phone
2. **Go to Telephony dashboard** → SIP Setup tab
3. **Generate QR code** for +2330247535969
4. **Scan with Linphone**
5. **Watch status change** to "Registered" ✅
6. **Make a test call** to your number!

## 💡 Pro Tips

- **Keep Linphone running** in background for incoming calls
- **Enable push notifications** in Linphone settings
- **Use WiFi** for most stable connection
- **Check "Keep alive"** option in Linphone account settings
- **Battery optimization** - exempt Linphone from battery saving

## 🐛 Troubleshooting

### QR Code Won't Scan
- Try manual configuration with credentials above
- Ensure QR code is fully visible on screen
- Update Linphone to latest version

### Registration Fails
- Check WiFi connection
- Verify credentials (case-sensitive)
- Try TCP instead of UDP in advanced settings
- Check firewall allows port 5060

### Status Shows "Not Registered"
- Wait 5 seconds for auto-refresh
- Click refresh button manually
- Restart Linphone app
- Re-scan QR code

## 📚 Related Documentation

- **Phone as Gateway Guide**: `/opt/kasaai/apps/shared/asterisk_api/PHONE_AS_GATEWAY_GUIDE.md`
- **Linphone Config**: `/opt/kasaai/apps/shared/asterisk_api/linphone-config.txt`
- **Asterisk Integration**: `/opt/kasaai/apps/shared/asterisk_api/INTEGRATION_REFERENCE.md`

## 🎉 Success!

You now have a complete SIP registration system with:
- ✅ QR code generation
- ✅ Real-time status monitoring
- ✅ ANT cellular gateway awareness
- ✅ Beautiful UI in Telephony dashboard

**Go try it out!** 📱 🎊
