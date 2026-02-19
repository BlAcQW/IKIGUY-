# ChurchFlow MVP - Minimum Viable Product Summary

**Version:** 1.0
**Date:** 2025-10-24
**Status:** Ready for Development
**Target Completion:** 6-8 Weeks
**First Deployment:** Single Church Pilot

---

## Executive Summary

The ChurchFlow MVP focuses on solving the **most critical pain point**: **bus transportation chaos during conferences**. By delivering a mobile app with smart bus coordination, real-time notifications, and QR code check-in, we enable a single church to run their next conference smoothly while gathering validation for future features.

### MVP Scope

✅ **In Scope** (Must-Have)
- Phone authentication (OTP via Supabase)
- Bus route creation and registration
- Conference registration with QR check-in
- Multi-channel notifications (SMS + Push via n8n)
- Mobile app (iOS + Android)
- Basic admin dashboard (web)

❌ **Out of Scope** (Phase 2+)
- AI voice kiosk "Ama"
- RAG-powered semantic search
- Advanced analytics
- Multi-church support
- Volunteer management
- Payment/donation integration

---

## Table of Contents

1. [MVP Vision](#mvp-vision)
2. [Success Criteria](#success-criteria)
3. [Core Features](#core-features)
4. [User Flows](#user-flows)
5. [Technical Implementation](#technical-implementation)
6. [Development Timeline](#development-timeline)
7. [Launch Plan](#launch-plan)
8. [Post-Launch Validation](#post-launch-validation)

---

## MVP Vision

**"Enable stress-free bus coordination and check-in for a single church's conference in 6-8 weeks"**

### The Problem We're Solving

**Before ChurchFlow**:
- Pastor Mensah maintains bus lists on WhatsApp & spreadsheets
- Members ask "Which bus am I on?" repeatedly
- Last-minute delays cause chaos (no quick way to notify everyone)
- Check-in queues waste 30+ minutes
- No accountability for no-shows

**After ChurchFlow MVP**:
- Members register for buses in the app
- Everyone knows their bus, time, and pickup location
- Coordinators send delay updates with one tap → SMS + Push
- Check-in takes <20 seconds via QR code
- Admins see real-time attendance data

### MVP Success = Validated Value

If after the first conference:
1. **70%+ of members** have the app installed
2. **85%+ of bus riders** registered via app (vs. WhatsApp)
3. **Check-in speed** reduced from 30+ min to <20 sec average
4. **User satisfaction** rating: 4.5/5 stars

Then we have **proven demand** and can confidently build Phase 2 (AI kiosk, multi-church, etc.).

---

## Success Criteria

### Quantitative Metrics

| Metric | Target | How Measured |
|--------|--------|--------------|
| **App Adoption** | 70% of active members (min 200 users) | Downloads + registrations |
| **Bus Pre-Registration** | 85% of bus riders | App registrations vs. manual list |
| **Check-In Speed** | <20 seconds average | Time from QR scan to confirmation |
| **Notification Delivery** | 95% within 2 minutes | SMS + Push delivery logs |
| **Admin Time Saved** | 50% reduction (anecdotal) | Coordinator feedback |
| **App Crashes** | <1% crash rate | Firebase Crashlytics |

### Qualitative Success Indicators

✅ **User Feedback**:
- "I knew exactly where to go and when"
- "Check-in was so fast!"
- "No more WhatsApp confusion"

✅ **Admin Feedback**:
- "Saved me hours of coordination"
- "Real-time updates were a game-changer"
- "I can see who's checked in instantly"

✅ **Stakeholder Buy-In**:
- Church leadership approves Phase 2 budget
- Other branches request access
- Testimonials for marketing

---

## Core Features

### 1. Authentication & User Profiles 👤

**Why it matters**: Secure identity for personalized experience

**Features**:
- Phone number + OTP login (Supabase Auth)
- User profile: name, branch, volunteer roles (optional)
- Profile photo upload (Supabase Storage)
- Simple onboarding flow (5 screens, <2 min)

**Technical Stack**:
- Supabase Auth for OTP delivery & JWT
- MongoDB for user profiles
- FastAPI `/auth/send-otp` and `/auth/verify-otp` endpoints

**Acceptance Criteria**:
- [ ] User can sign up with phone number in <2 minutes
- [ ] OTP received within 30 seconds
- [ ] Invalid OTP shows clear error message
- [ ] Session persists for 30 days (refresh token)
- [ ] User can update profile info anytime

---

### 2. Bus Transportation Coordination 🚌

**Why it matters**: Core value proposition — solves biggest pain point

#### 2.1 Bus Route Management (Admin)

**Features**:
- Create bus routes with:
  - Name (e.g., "Legon Bus #1")
  - Pickup location (text + map coordinates)
  - Departure time
  - Capacity (default: 50)
  - Driver name & phone
- View all routes with capacity indicators (bar charts)
- Edit/delete routes (can't delete if members registered)
- Export passenger list (Excel)

**UI**: Admin dashboard (React web app)

**Acceptance Criteria**:
- [ ] Admin can create a bus route in <1 minute
- [ ] Capacity bar shows green (<75%), yellow (75-95%), red (95-100%)
- [ ] Can't delete route with active registrations
- [ ] Export generates Excel with columns: Name, Phone, Branch, Seat #

#### 2.2 Bus Registration (Member)

**Features**:
- Browse buses by conference and pickup location
- See: name, departure time, capacity, distance from user (optional)
- Register with one tap → Get QR code boarding pass
- View "My Routes" with real-time status
- Cancel registration (up to 2 hours before departure)

**User Flow**:
```
Home → Select Conference → Choose Pickup Location →
See Available Buses → Tap "Register" → Confirmation Screen with QR Code
```

**Acceptance Criteria**:
- [ ] User can register in <30 seconds
- [ ] QR code generated immediately
- [ ] Push notification sent: "You're registered for Legon Bus #1..."
- [ ] When bus full, auto-moved to next available bus + notified
- [ ] Cancel button shows confirmation dialog

#### 2.3 Real-Time Bus Updates (Coordinator)

**Features**:
- Select bus route → Tap "Send Update"
- Update types: Delay (enter minutes), Cancellation, Departure, Arrival
- Notification sent to all registered members on that bus only
- Multi-channel: SMS (if delay >15 min) + Push (always)
- View delivery status (sent/delivered/failed)

**Technical Stack**:
- n8n workflow (`@apps/shared/integration/n8n.py`) for orchestration
- Twilio for SMS
- Firebase Cloud Messaging for Push
- MongoDB `NotificationLogs` collection

**Acceptance Criteria**:
- [ ] Coordinator sends delay update in <30 seconds
- [ ] 95% of notifications delivered within 2 minutes
- [ ] Only registered members on that bus receive notification
- [ ] Delivery failures logged and retried (3 attempts)

---

### 3. Conference Registration & Check-In 🎫

#### 3.1 Conference Creation (Admin)

**Features**:
- Create conference with:
  - Name, description
  - Start/end dates
  - Venue name + address
  - Banner image upload
  - Max capacity (optional)
- Publish/unpublish toggle
- View registration count

**Acceptance Criteria**:
- [ ] Admin creates conference in <3 minutes
- [ ] Image upload works (drag & drop or file picker)
- [ ] Published conferences appear in member app immediately
- [ ] Registration count updates in real-time

#### 3.2 Conference Registration (Member)

**Features**:
- View conference details (banner, description, venue, dates)
- Register with one tap
- Auto-generate QR code for check-in
- Save QR to phone (screenshot or Apple/Google Wallet)
- Get reminder notifications (7 days, 3 days, 1 day, 3 hours before)

**User Flow**:
```
Home Screen (Conference Banner) → Tap → Conference Details →
"Register" Button → Success Screen with QR Code → Save/Share
```

**Acceptance Criteria**:
- [ ] Registration takes <15 seconds
- [ ] QR code is unique per user per conference
- [ ] Push notification: "You're registered for Impact 2025!"
- [ ] Calendar invite button works (Google/Apple)

#### 3.3 QR Code Check-In (Admin/Usher)

**Features**:
- Admin dashboard with QR scanner (webcam or mobile camera)
- Scan QR → Instant check-in confirmation (green checkmark)
- Fallback: Search by phone number or name
- Manual check-in override
- Real-time attendance counter
- View checked-in members list (searchable)

**Technical Stack**:
- React webcam library for QR scanning
- FastAPI `/conferences/{id}/check-in` endpoint
- MongoDB atomic update to prevent double check-ins

**Acceptance Criteria**:
- [ ] QR scan → check-in in <3 seconds
- [ ] Duplicate scan shows "Already checked in" message
- [ ] Search works for partial names and phone numbers
- [ ] Attendance count updates instantly on admin dashboard
- [ ] Works offline (queue check-ins, sync when online)

---

### 4. Notifications 📱

**Why it matters**: Timely communication is critical for event success

**Features**:
- Multi-channel routing based on urgency:
  - **Critical** (delay >30 min): SMS + Push + WhatsApp
  - **High** (delay 15-30 min): SMS + Push
  - **Medium** (<15 min delay): Push only
  - **Low** (reminders): Push + Email
- Notification history in app (grouped by date)
- Mark as read/unread
- Deep links to relevant screens (bus details, conference info)
- Opt-out settings (can't disable SMS for critical alerts)

**Technical Stack**:
- n8n workflows (`@apps/shared/integration/n8n.py`) for orchestration
- Twilio (SMS + WhatsApp)
- Firebase Cloud Messaging (Push)
- SendGrid (Email)
- MongoDB `NotificationLogs` collection

**Notification Templates**:
```python
{
    "bus_delay": "Bus {bus_name} delayed by {delay_minutes} minutes. New ETA: {new_time}. Pickup: {location}. Sorry for the inconvenience!",

    "bus_departure": "Your bus is now departing from {location}. Safe travels!",

    "bus_cancellation": "Unfortunately, Bus {bus_name} has been cancelled. We've moved you to {new_bus_name} departing at {new_time}.",

    "conference_reminder_7d": "📅 Impact 2025 is in 7 days! Dec 20-22. Your bus departs at {bus_time} from {location}.",

    "conference_reminder_1d": "🎉 Impact 2025 is tomorrow! Make sure you're ready. Your bus: {bus_name} at {time} from {location}.",

    "check_in_confirmation": "✅ You're checked in to Impact 2025! Enjoy the conference."
}
```

**Acceptance Criteria**:
- [ ] 95% delivery rate within 2 minutes
- [ ] SMS works for Ghanaian numbers (+233)
- [ ] Push notifications show on lock screen
- [ ] Tapping notification opens relevant screen
- [ ] Failed deliveries retried 3 times

---

### 5. Mobile App (iOS & Android) 📱

**Platform**: React Native (Expo) for cross-platform development

**Key Screens**:

#### 5.1 Home Screen
```
┌──────────────────────────────┐
│  👤  ChurchFlow        🔔    │
├──────────────────────────────┤
│  🎪 Impact 2025              │  ← Conference Banner
│  Dec 20-22, 2025             │
│  [Register Now]              │
├──────────────────────────────┤
│  🚌 My Bus                   │  ← If registered
│  Legon Bus #1                │
│  Departs: 5:30 PM            │
│  Status: On Time ✅          │
├──────────────────────────────┤
│  📢 Recent Notifications     │
│  • Bus departure reminder    │
│  • New event posted          │
│  [View All]                  │
└──────────────────────────────┘
```

#### 5.2 Bus Registration Flow
1. Select Conference
2. Choose Pickup Location (dropdown or map)
3. View Available Buses (cards with capacity bars)
4. Confirm Registration
5. Success (QR code + save button)

#### 5.3 Conference Details
- Banner image
- Description
- Venue + "View on Map" button
- Registration button
- "My QR Code" tab (if registered)

#### 5.4 Notifications Tab
- Grouped by date (Today, Yesterday, This Week)
- Filter by type (All, Bus, Conference)
- Swipe to delete
- Tap to view details (deep link)

#### 5.5 Profile
- User info (name, phone, branch)
- Profile photo
- Notification preferences
- Logout button

**Technical Stack**:
- React Native (Expo)
- TypeScript
- React Navigation
- Axios (API client)
- AsyncStorage (local storage)
- Firebase Cloud Messaging

**Acceptance Criteria**:
- [ ] Works on iOS 13+ and Android 8+
- [ ] App size <30 MB
- [ ] Launches in <3 seconds
- [ ] Offline mode: View cached data, queue actions
- [ ] Push notifications work when app in background

---

### 6. Admin Dashboard (Web) 💻

**Platform**: React (Vite) + Tailwind CSS

**Pages**:

#### 6.1 Bus Management
- List all bus routes (table view)
- Create/Edit/Delete buttons
- Capacity indicators (progress bars)
- "Send Update" button per bus
- Passenger list (expandable)
- Export to Excel

#### 6.2 Conference Management
- List all conferences
- Create/Edit buttons
- Registration count per conference
- Check-in interface (QR scanner + search)
- Attendance stats (pie chart: Registered vs Checked-in vs No-show)

#### 6.3 Users (Basic)
- View all users (table)
- Search by name or phone
- Assign roles (dropdown)
- Basic analytics (total users, active users)

**Technical Stack**:
- React 18 + TypeScript
- Vite (build tool)
- Tailwind CSS
- shadcn/ui components
- Recharts (for basic charts)
- React Webcam (QR scanner)

**Acceptance Criteria**:
- [ ] Responsive design (desktop + tablet)
- [ ] Fast page loads (<2 seconds)
- [ ] Real-time updates (WebSocket or polling)
- [ ] Works on Chrome, Safari, Edge

---

## User Flows

### Flow 1: Member Registers for Bus

```
┌─────────────────────────────────────────────────────────┐
│  Actor: Church Member (Akosua)                          │
│  Goal: Register for bus to Impact 2025 conference       │
└─────────────────────────────────────────────────────────┘

1. Akosua opens ChurchFlow app on her phone
   ↓
2. Home screen shows "Impact 2025" conference banner
   ↓
3. Taps banner → Conference details screen
   ↓
4. Taps "Register for Bus" button
   ↓
5. Selects pickup location: "Legon Mall"
   ↓
6. Sees list of buses:
   - Legon Bus #1 | 5:30 PM | 45/50 seats | 2 km away
   - Legon Bus #2 | 6:00 PM | 30/50 seats | 2 km away
   ↓
7. Taps "Legon Bus #1" → "Register"
   ↓
8. Success screen appears:
   - "You're registered for Legon Bus #1!"
   - QR code displayed
   - "Save to Wallet" button
   - "Share" button
   ↓
9. Push notification sent: "Registration confirmed..."
   ↓
10. Returns to home screen → "My Bus" card now shows "Legon Bus #1"

✅ Total time: ~45 seconds
```

---

### Flow 2: Coordinator Sends Bus Delay Update

```
┌─────────────────────────────────────────────────────────┐
│  Actor: Transport Coordinator (Kwame)                   │
│  Goal: Notify members that bus is delayed by 30 minutes │
└─────────────────────────────────────────────────────────┘

1. Kwame opens admin dashboard on laptop
   ↓
2. Goes to "Bus Management" page
   ↓
3. Sees list of buses with status indicators
   ↓
4. Clicks "Legon Bus #1" → "Send Update" button
   ↓
5. Modal appears: "Update Type: [Delay ▼]"
   ↓
6. Enters: "30" minutes
   ↓
7. Optional message field: "Traffic on Spintex Road. Sorry!"
   ↓
8. Clicks "Send Notification" button
   ↓
9. System triggers n8n workflow:
   - Since delay >30 min → SMS + Push + WhatsApp
   ↓
10. 45 registered members receive notifications within 2 minutes
    ↓
11. Dashboard shows: "45/45 notifications delivered ✅"
    ↓
12. Kwame sees delivery log:
    - 45 SMS sent (44 delivered, 1 failed)
    - 45 Push sent (43 delivered, 2 not opened)
    - 45 WhatsApp sent (40 delivered)

✅ Total time: ~60 seconds from decision to delivery
```

---

### Flow 3: Usher Checks In Members via QR

```
┌─────────────────────────────────────────────────────────┐
│  Actor: Usher (at conference entrance)                  │
│  Goal: Check in 200 members in <20 minutes              │
└─────────────────────────────────────────────────────────┘

1. Usher opens admin dashboard on iPad
   ↓
2. Goes to "Impact 2025 Conference" → "Check-In" tab
   ↓
3. QR scanner interface appears (webcam active)
   ↓
4. Member (Akosua) shows QR code on phone
   ↓
5. Usher scans QR code
   ↓
6. System validates QR:
   - Checks if valid for this conference
   - Checks if already checked in
   ↓
7. Screen shows: "✅ Akosua Mensah - CHECKED IN"
   - Green checkmark animation
   - Photo (if uploaded)
   - Branch: Legon
   - Seat: Legon Bus #1, Seat 12
   ↓
8. Attendance counter updates: "152/1234 checked in"
   ↓
9. Next member steps up → Repeat

✅ Average time per check-in: ~5 seconds (if smooth scanning)
✅ Fallback: If QR doesn't scan, usher searches by phone number
```

---

## Technical Implementation

### Architecture Overview

```
┌────────────────────────────────────┐
│    Mobile App (React Native)       │
│    + Admin Dashboard (React)       │
└───────────┬────────────────────────┘
            │ HTTPS API Calls
            ▼
┌────────────────────────────────────┐
│   Nginx (church.kasaai.com)        │
└───────────┬────────────────────────┘
            │
            ▼
┌────────────────────────────────────┐
│   FastAPI Backend (Python 3.11)    │
│   - Routes, Services, Models       │
└──┬──────┬──────┬──────┬───────────┘
   │      │      │      │
   ▼      ▼      ▼      ▼
┌────┐ ┌────┐ ┌────┐ ┌────────────┐
│Mongo│ │Supa│ │n8n │ │Twilio/FCM  │
│DB  │ │base│ │    │ │            │
└────┘ └────┘ └────┘ └────────────┘
```

### Tech Stack Decisions (MVP)

| Component | Technology | Rationale |
|-----------|-----------|-----------|
| **Backend** | FastAPI + Python | Fast, async, type-safe, team expertise |
| **Database** | MongoDB | Flexible schema, fast writes, JSON-native |
| **Auth** | Supabase Auth | Phone OTP out-of-box, JWT, reliable |
| **Storage** | Supabase Storage | Images (profiles, banners), CDN |
| **Mobile** | React Native (Expo) | Cross-platform, fast dev, OTA updates |
| **Admin** | React + Vite | Modern, fast, same language as mobile |
| **Notifications** | n8n + Twilio + FCM | Workflow orchestration, multi-channel |
| **Hosting** | VPS (existing infra) | Cost-effective, controlled |

### Key Integrations (Leveraging Shared Services)

#### 1. n8n Workflow Orchestration (`@apps/shared/integration/n8n.py`)

**Purpose**: Multi-channel notification routing

**Implementation**:
```python
from apps.shared.integration.n8n import N8NIntegration

n8n = N8NIntegration()

# Create bus delay workflow (one-time setup)
workflow = await n8n.create_workflow(
    name="ChurchFlow - Bus Delay Notification",
    trigger={"type": "webhook", "path": "churchflow/bus-delay"},
    nodes=[
        {
            "type": "switch",
            "condition": "delay_minutes >= 30",
            "branches": {
                "true": ["sms_node", "push_node", "whatsapp_node"],
                "false": ["push_node"]
            }
        },
        {
            "id": "sms_node",
            "type": "twilio_sms",
            "credentials": "twilio_churchflow",
            "parameters": {
                "to": "={{$json.phone}}",
                "message": "Bus {{$json.bus_name}} delayed {{$json.delay_minutes}} min. New ETA: {{$json.new_time}}. Pickup: {{$json.location}}. Sorry for the inconvenience!"
            }
        },
        {
            "id": "push_node",
            "type": "firebase_push",
            "credentials": "fcm_churchflow",
            "parameters": {
                "token": "={{$json.fcm_token}}",
                "title": "Bus Delay - {{$json.bus_name}}",
                "body": "Delayed by {{$json.delay_minutes}} minutes. Tap for details.",
                "data": {
                    "type": "bus_update",
                    "bus_route_id": "={{$json.bus_route_id}}"
                }
            }
        }
    ]
)

# Trigger workflow when sending notifications
for user in bus_registered_users:
    await n8n.execute_workflow_webhook(
        workflow_name="churchflow/bus-delay",
        data={
            "phone": user.phone,
            "fcm_token": user.fcm_token,
            "delay_minutes": 30,
            "bus_name": "Legon Bus #1",
            "new_time": "6:00 PM",
            "location": "Legon Mall",
            "bus_route_id": str(bus_route.id)
        }
    )
```

**Benefits**:
- No need to integrate Twilio/FCM directly in app code
- Visual workflow editor for changing logic
- Built-in retry and error handling
- Delivery logs for monitoring

#### 2. Supabase Auth & Storage

**Auth** (`@apps/shared/integration/supabase.py` + Supabase JS SDK):
```python
from supabase import create_client

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Send OTP
await supabase.auth.sign_in_with_otp({
    "phone": "+233201234567"
})

# Verify OTP and get session
session = await supabase.auth.verify_otp({
    "phone": "+233201234567",
    "token": "123456",
    "type": "sms"
})

# Extract JWT for API calls
jwt = session.access_token
```

**Storage** (for profile photos, conference banners):
```python
# Upload file
file_path = await supabase.storage.from_("churchflow-images").upload(
    path=f"profiles/{user_id}.jpg",
    file=image_bytes
)

# Get public URL
url = supabase.storage.from_("churchflow-images").get_public_url(file_path)
```

#### 3. MongoDB Schema Design

```python
# users collection
{
    "_id": ObjectId,
    "phone": "+233201234567",  # Indexed, unique
    "name": "Akosua Mensah",
    "branch_id": ObjectId,
    "branch_name": "Legon",  # Denormalized for faster reads
    "roles": ["member"],  # RBAC
    "volunteer_roles": ["choir", "usher"],
    "profile_image_url": "https://...",
    "fcm_token": "...",
    "created_at": ISODate,
    "last_active": ISODate
}

# bus_routes collection
{
    "_id": ObjectId,
    "name": "Legon Bus #1",
    "pickup_location": "Legon Mall",
    "pickup_coordinates": {"type": "Point", "coordinates": [-0.1870, 5.6484]},
    "departure_time": ISODate,
    "capacity": 50,
    "registered_count": 45,  # Updated via aggregation or counter
    "conference_id": ObjectId,
    "driver_name": "Kwame Asante",
    "driver_phone": "+233501234567",
    "status": "scheduled",
    "created_at": ISODate
}

# bus_registrations collection
{
    "_id": ObjectId,
    "user_id": ObjectId,  # Compound index: (user_id, bus_route_id)
    "bus_route_id": ObjectId,
    "conference_id": ObjectId,
    "seat_number": 12,
    "checked_in": false,
    "qr_code": "BR-ABC123DEF",  # Unique, indexed
    "created_at": ISODate
}

# conferences collection
{
    "_id": ObjectId,
    "name": "Impact 2025",
    "description": "...",
    "start_date": ISODate,
    "end_date": ISODate,
    "venue": "National Theatre, Accra",
    "banner_image_url": "https://...",
    "max_capacity": 5000,
    "registration_count": 1234,  # Updated via counter
    "published": true,
    "created_by": ObjectId,
    "created_at": ISODate
}

# conference_registrations collection
{
    "_id": ObjectId,
    "user_id": ObjectId,  # Compound index: (user_id, conference_id)
    "conference_id": ObjectId,
    "checked_in": false,
    "check_in_time": null,
    "check_in_method": null,  # "qr", "phone", "manual"
    "qr_code": "CF-XYZ789ABC",  # Unique, indexed
    "created_at": ISODate
}

# notification_logs collection
{
    "_id": ObjectId,
    "user_id": ObjectId,
    "template_type": "bus_delay",
    "channel": "sms",  # "sms", "push", "whatsapp", "email"
    "message": "Bus Legon #1 delayed...",
    "sent_at": ISODate,
    "delivered": true,
    "delivered_at": ISODate,
    "error_message": null
}
```

### API Endpoints (MVP)

```
# Authentication
POST   /api/v1/auth/send-otp          # Send OTP to phone
POST   /api/v1/auth/verify-otp        # Verify OTP, return JWT
POST   /api/v1/auth/refresh           # Refresh access token

# Users
GET    /api/v1/users/me               # Get current user
PUT    /api/v1/users/me               # Update current user
POST   /api/v1/users/me/photo         # Upload profile photo

# Conferences
GET    /api/v1/conferences            # List published conferences
GET    /api/v1/conferences/{id}       # Get conference details
POST   /api/v1/conferences            # Create conference (admin)
PUT    /api/v1/conferences/{id}       # Update conference (admin)
POST   /api/v1/conferences/{id}/register  # Register for conference
POST   /api/v1/conferences/{id}/check-in  # Check in user (QR or phone)

# Buses
GET    /api/v1/buses/routes           # List routes (filterable by conference)
GET    /api/v1/buses/routes/{id}      # Get route details
POST   /api/v1/buses/routes           # Create route (coordinator)
PUT    /api/v1/buses/routes/{id}      # Update route (coordinator)
POST   /api/v1/buses/register         # Register for bus
DELETE /api/v1/buses/register/{id}    # Cancel registration
GET    /api/v1/buses/my-routes        # User's registered buses
POST   /api/v1/buses/updates          # Send bus update (coordinator)

# Notifications
GET    /api/v1/notifications/history  # User's notification history
PUT    /api/v1/notifications/preferences  # Update preferences
```

### Mobile App Structure

```
churchflow-mobile/
├── src/
│   ├── screens/
│   │   ├── auth/
│   │   │   ├── PhoneEntryScreen.tsx
│   │   │   ├── OTPVerificationScreen.tsx
│   │   │   └── ProfileSetupScreen.tsx
│   │   ├── home/
│   │   │   └── HomeScreen.tsx
│   │   ├── buses/
│   │   │   ├── BusListScreen.tsx
│   │   │   ├── BusRegistrationScreen.tsx
│   │   │   └── MyRoutesScreen.tsx
│   │   ├── conferences/
│   │   │   ├── ConferenceDetailsScreen.tsx
│   │   │   └── QRCodeScreen.tsx
│   │   ├── notifications/
│   │   │   └── NotificationsScreen.tsx
│   │   └── profile/
│   │       └── ProfileScreen.tsx
│   ├── components/
│   │   ├── BusCard.tsx
│   │   ├── ConferenceBanner.tsx
│   │   ├── QRCodeDisplay.tsx
│   │   └── NotificationItem.tsx
│   ├── navigation/
│   │   └── AppNavigator.tsx
│   ├── services/
│   │   ├── api.ts           # Axios client
│   │   ├── auth.ts          # Auth logic
│   │   └── notifications.ts # FCM handling
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useBuses.ts
│   │   └── useConferences.ts
│   ├── contexts/
│   │   └── AuthContext.tsx
│   ├── types/
│   │   └── index.ts         # TypeScript types
│   └── utils/
│       └── formatters.ts
├── app.json
├── package.json
└── tsconfig.json
```

---

## Development Timeline

### Week 1-2: Foundation

**Backend**:
- [x] Project setup (FastAPI, MongoDB, Supabase)
- [ ] Authentication endpoints (OTP send/verify)
- [ ] User model and profile endpoints
- [ ] Database schema setup with indexes
- [ ] Environment config

**Mobile**:
- [ ] Expo project init
- [ ] Navigation setup (React Navigation)
- [ ] Auth screens (Phone, OTP, Profile)
- [ ] API service layer
- [ ] Auth context and storage

**Admin**:
- [ ] React + Vite project setup
- [ ] Basic layout and routing
- [ ] Login page

**Deliverables**:
- ✅ Users can sign up and log in
- ✅ JWT auth working
- ✅ Profile CRUD endpoints

---

### Week 3-4: Bus Transportation

**Backend**:
- [ ] Bus route CRUD endpoints
- [ ] Bus registration logic with capacity tracking
- [ ] Auto-assignment algorithm
- [ ] n8n workflow integration for notifications
- [ ] Unit tests (pytest)

**Mobile**:
- [ ] Bus list screen with filters
- [ ] Bus registration flow (5 screens)
- [ ] QR code display for boarding pass
- [ ] "My Routes" screen
- [ ] Push notification handling

**Admin**:
- [ ] Bus management page (CRUD interface)
- [ ] Passenger list view
- [ ] Send update modal
- [ ] Capacity indicators

**Deliverables**:
- ✅ Members can register for buses
- ✅ Coordinators can send delay updates
- ✅ Notifications delivered via SMS + Push

---

### Week 5-6: Conferences & Check-In

**Backend**:
- [ ] Conference CRUD endpoints
- [ ] Conference registration logic
- [ ] QR code generation (unique per user per event)
- [ ] Check-in endpoint with validation
- [ ] Real-time attendance counting

**Mobile**:
- [ ] Conference details screen
- [ ] Conference registration flow
- [ ] QR code screen with save/share
- [ ] Reminder notifications (scheduled)

**Admin**:
- [ ] Conference management page
- [ ] QR scanner interface (react-webcam + jsQR)
- [ ] Search by phone/name fallback
- [ ] Attendance dashboard (charts)

**Deliverables**:
- ✅ Members can register for conferences
- ✅ Admins can check in users via QR
- ✅ Real-time attendance stats

---

### Week 7-8: Polish, Testing, Deployment

**All Platforms**:
- [ ] UI polish (animations, loading states, error handling)
- [ ] Offline mode (AsyncStorage caching, queue actions)
- [ ] Comprehensive testing:
  - [ ] Unit tests (Jest/Pytest)
  - [ ] Integration tests (API endpoints with real MongoDB)
  - [ ] E2E tests (Detox for mobile, Playwright for admin)
- [ ] Performance optimization (image compression, lazy loading)
- [ ] Accessibility (screen reader, high contrast)
- [ ] Documentation (API docs, user guides)

**Deployment**:
- [ ] Backend deployed to production VPS
- [ ] Nginx config + SSL setup
- [ ] MongoDB backups configured
- [ ] Mobile apps on TestFlight (iOS) + Play Store Beta (Android)
- [ ] Admin dashboard hosted
- [ ] Monitoring (Sentry for errors, custom health checks)

**Deliverables**:
- ✅ Production-ready MVP
- ✅ All acceptance criteria met
- ✅ Training materials prepared

---

## Launch Plan

### Pre-Launch (1 Week Before)

**1. Beta Testing**:
- Recruit 50 beta users from church
- Distribute TestFlight/Play Store Beta links via WhatsApp
- Run test event (small gathering, 50-100 people)
- Collect feedback via in-app survey

**2. Admin Training**:
- 2-hour workshop with transport coordinators and conference admins
- Cover:
  - Creating bus routes
  - Sending updates
  - QR check-in process
  - Troubleshooting common issues
- Provide video tutorials and PDF quick start guides

**3. Marketing**:
- Announcement during Sunday service (pastor endorsement)
- Posters with QR code to download app
- WhatsApp broadcast to all groups
- SMS blast: "Download ChurchFlow for Impact 2025..."
- Demo video on church website and social media

**4. Technical Prep**:
- Load testing (simulate 500 concurrent users)
- SMS credit check (ensure sufficient balance)
- Backup plan if SMS fails (WhatsApp group fallback)
- 24/7 on-call developer assigned

---

### Launch Day (Conference Event)

**T-7 Days**:
- Reminder push notification: "Impact 2025 is in 7 days!"
- Bus registration deadline reminder

**T-1 Day**:
- Final reminder: "Tomorrow is Impact 2025! Your bus: Legon #1 at 5:30 PM."

**Event Morning**:
- Check-in kiosks set up (2-3 iPads with admin dashboard)
- QR scanners tested
- Coordinators on standby with app open
- Manual check-in list as fallback (printed from admin dashboard)

**During Event**:
- Monitor notification delivery rates (dashboard)
- Coordinators send real-time updates as needed
- Collect anecdotal feedback from members

**Post-Event**:
- In-app survey: "How was your experience?"
- Thank you push notification
- Export attendance report for church records

---

### Post-Launch (Week 1-2)

**1. Data Analysis**:
- Review success metrics:
  - App downloads vs. target (70%)
  - Bus pre-registration rate (85%)
  - Check-in speed (avg seconds)
  - Notification delivery (95%)
- Identify bottlenecks (e.g., slow QR scanning)

**2. User Feedback**:
- Analyze in-app survey responses
- Conduct 5-10 user interviews (members, coordinators, admins)
- Prioritize top 5 requested features for next iteration

**3. Technical Improvements**:
- Fix critical bugs discovered during event
- Optimize slow API endpoints
- Improve error messages based on user confusion

**4. Stakeholder Presentation**:
- Present results to church leadership
- Share success stories and testimonials
- Propose Phase 2 roadmap (AI kiosk, multi-church, etc.)
- Request approval for continued development

---

## Post-Launch Validation

### Decision Framework

**Criteria for Phase 2 Go/No-Go**:

✅ **GO** if:
1. **70%+ app adoption** → Proven demand
2. **4.5/5 star rating** → Users love it
3. **50%+ admin time saved** → Clear value
4. **Church leadership enthusiastic** → Willing to invest
5. **No critical bugs** → Technical foundation solid

❌ **NO-GO** if:
1. **<50% app adoption** → Reconsider approach
2. **<4.0 rating** → Major UX issues
3. **Negative admin feedback** → Not solving problem
4. **Technical debt too high** → Need refactoring before scaling

### Pivot Scenarios

**If low app adoption (<50%)**:
- Investigate: Was marketing insufficient? App too complex? WhatsApp groups preferred?
- Pivot: Focus on admin tools only (bus coordination dashboard, no mobile app)

**If notification failures high (>10%)**:
- Investigate: SMS delivery issues? FCM token problems? n8n workflow bugs?
- Pivot: Simplify to single-channel (Push only, SMS backup)

**If check-in too slow (>30 sec avg)**:
- Investigate: QR scanning issues? Network latency? Manual overrides too frequent?
- Pivot: Pre-printed QR codes, NFC tags, or simplified manual check-in

---

## Summary: What Makes This MVP Successful?

1. **Laser Focus** - Solves ONE big problem (bus chaos) extremely well
2. **Leverage Existing Services** - n8n, Supabase, shared integrations (no reinventing wheels)
3. **Mobile-First** - Where users are (not desktop)
4. **Validate Demand** - Single church pilot before scaling
5. **Clear Success Metrics** - Know when we've succeeded or need to pivot
6. **Rapid Iteration** - 6-8 weeks to real-world test

### MVP Checklist

Before declaring MVP "done", verify:

- [ ] User can sign up and log in in <2 minutes
- [ ] User can register for bus in <30 seconds
- [ ] User receives QR code boarding pass
- [ ] Coordinator can send delay update in <60 seconds
- [ ] 95% of notifications delivered within 2 minutes
- [ ] User can register for conference in <15 seconds
- [ ] Admin can check in user via QR in <5 seconds
- [ ] Mobile app works offline (view cached data)
- [ ] Admin dashboard real-time updates work
- [ ] All critical user flows have <1% crash rate
- [ ] API response times <500ms for 95th percentile
- [ ] MongoDB indexes created for all queries
- [ ] Error monitoring set up (Sentry)
- [ ] User guide PDF and videos created
- [ ] Admin training completed

---

**Ready to Build?** 🚀

This MVP is scoped for **6-8 weeks of focused development**. Every feature has clear business value, acceptance criteria, and validation metrics. Let's build something church members will love!

---

**Next Steps**:

1. ✅ Review and approve this MVP scope
2. ⏭️ Kick off Sprint 0: Shared services integration testing
3. ⏭️ Start Week 1-2: Foundation development
4. ⏭️ Recruit beta users (50 members)
5. ⏭️ Set first milestone: Working authentication in 2 weeks

**Questions or Adjustments?**

If any part of this MVP seems too ambitious for 6-8 weeks, we can de-scope further. The goal is **one successful conference** with **proven value** before investing in Phase 2.

---

**End of MVP Document**
