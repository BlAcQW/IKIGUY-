# ChurchFlow - Product Requirements Document (PRD)

**Version:** 1.0
**Date:** 2025-10-24
**Status:** Draft
**Product Owner:** AI Labs Africa
**Target Launch:** Q2 2025

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Product Vision](#product-vision)
3. [Problem Statement](#problem-statement)
4. [Target Users](#target-users)
5. [Product Goals & Success Metrics](#product-goals--success-metrics)
6. [Functional Requirements](#functional-requirements)
7. [Technical Architecture](#technical-architecture)
8. [User Experience & Design](#user-experience--design)
9. [Security & Privacy](#security--privacy)
10. [Integration Points](#integration-points)
11. [Release Strategy](#release-strategy)
12. [Risk Assessment](#risk-assessment)

---

## Executive Summary

**ChurchFlow** is a mobile-first church management and event coordination platform that transforms how churches organize transportation, manage conferences, and connect with members. By combining intuitive mobile experiences with AI-powered personalization, ChurchFlow makes large-scale event coordination feel personal and effortless.

### Key Differentiators

🎯 **Smart Bus Coordination** - Auto-assignment, real-time updates, capacity management
🤖 **AI Voice Assistant "Ama"** - Personalized greetings in English & Twi using member history
📱 **Multi-Channel Notifications** - Intelligent routing (SMS/Push/WhatsApp/Email) based on urgency
🎫 **Seamless Check-in** - QR codes, voice kiosk, or manual with instant confirmation
🌍 **African-First Design** - Built for African churches with local languages & cultural awareness

### Market Opportunity

- **Target Market**: Churches with 500+ members organizing conferences/events
- **Initial Focus**: Ghana (English & Twi), expandable to West Africa
- **Revenue Model**: Freemium (self-hosted) → SaaS subscription (multi-church platform)
- **Competitive Advantage**: Only solution combining AI kiosk, voice AI, and smart transportation

---

## Product Vision

### 5-Year Vision

"To become the de facto church operations platform across Africa, making church administration so intuitive and personal that technology becomes invisible, allowing ministry leaders to focus on what matters most: people."

### Product Positioning

**ChurchFlow is to church management what Slack is to team communication**
- Intuitive, mobile-first, delightful to use
- Powerful enough for enterprise, simple enough for volunteers
- AI-enhanced but human-centered

### Core Values

1. **Warmth Over Efficiency** - Technology should enhance connection, not replace it
2. **Simplicity First** - Non-technical users should feel empowered
3. **African Context** - Designed for African churches, languages, and culture
4. **Privacy Respect** - Minimal data collection, maximum value
5. **Accessibility** - Works on low-end devices with limited connectivity

---

## Problem Statement

### Current Pain Points

#### For Church Members 👥
1. **Transportation Confusion** - "Which bus am I on? When does it leave? Where do I wait?"
2. **Information Overload** - Multiple WhatsApp groups, emails, announcements
3. **Check-in Delays** - Long lines at conference registration
4. **Feeling Anonymous** - Lost in large crowds, no personal recognition

#### For Church Administrators 🏛️
1. **Bus Coordination Chaos** - Manual tracking on spreadsheets, last-minute changes
2. **Communication Challenges** - Reaching all members quickly during delays
3. **No Real-Time Visibility** - Who's checked in? How many buses are full?
4. **Volunteer Burnout** - Manual processes, repetitive tasks

#### For Conference Organizers 🎪
1. **Registration Bottlenecks** - Manual check-in creates queues
2. **No Attendance Analytics** - Hard to track participation patterns
3. **Last-Minute Changes** - Difficult to communicate speaker changes or room updates

### The Cost of Inaction

Without ChurchFlow, churches experience:
- **Member Frustration** → Lower event attendance (15-20% no-show rate)
- **Admin Overwhelm** → Volunteer burnout and errors
- **Missed Connections** → Members feel like numbers, not people
- **Safety Concerns** → No accountability for who's on which bus

---

## Target Users

### Primary Personas

#### 1. **Akosua - The Active Member** 👤
- **Age**: 28, marketing professional
- **Tech Savvy**: High (smartphone user, social media active)
- **Needs**:
  - Know which bus she's on without asking
  - Get reminders so she doesn't miss departure
  - Quick check-in at conferences
  - Stay updated on schedule changes
- **Pain Points**:
  - Forgets to check WhatsApp groups
  - Arrives late to bus pickup points
  - Wastes time in check-in lines
- **Goals**: Attend events stress-free, stay informed

#### 2. **Pastor Mensah - The Branch Pastor** 👨‍💼
- **Age**: 45, branch leader
- **Tech Savvy**: Medium (uses WhatsApp, basic spreadsheets)
- **Needs**:
  - Track member attendance and engagement
  - Communicate quickly with branch members
  - Manage volunteer schedules
  - Access analytics for planning
- **Pain Points**:
  - Hard to track who attended what
  - Multiple tools for different tasks
  - Time-consuming manual processes
- **Goals**: Shepherd members effectively, reduce admin burden

#### 3. **Kwame - The Transport Coordinator** 🚌
- **Age**: 38, logistics professional
- **Tech Savvy**: Medium-high
- **Needs**:
  - Real-time view of bus capacity and registrations
  - Send delay notifications quickly
  - Check passengers in/out
  - Optimize routes and schedules
- **Pain Points**:
  - Spreadsheets don't update in real-time
  - Hard to notify everyone at once
  - No accountability for no-shows
- **Goals**: Smooth transportation, zero confusion, on-time departures

#### 4. **Elder Grace - The Super Admin** 👩‍💼
- **Age**: 52, church administrator
- **Tech Savvy**: Medium (learns quickly when motivated)
- **Needs**:
  - Oversee all branches and events
  - Manage permissions and roles
  - Access system-wide reports
  - Configure notification templates
- **Pain Points**:
  - No unified view across branches
  - Depends on IT support for changes
  - Hard to get accurate attendance data
- **Goals**: Efficient operations, data-driven decisions, empowered team

### Secondary Personas

- **Volunteer Ushers** - Need simple check-in tools
- **Conference Speakers** - Want to see their session info and audience size
- **Youth Leaders** - Coordinate youth events and activities
- **First-Time Visitors** - Need clear guidance and welcoming experience

---

## Product Goals & Success Metrics

### North Star Metric

**Member Engagement Score (MES)** = (Events Attended × Check-in Speed × Satisfaction Rating) / Total Events

### Goals by Phase

#### Phase 1: MVP (First 6 Months)
**Goal**: Prove core value proposition with single church deployment

| Metric | Target | Measurement |
|--------|--------|-------------|
| Member Adoption | 70% of active members | App downloads + registration |
| Bus Registration Rate | 85% of bus riders | Pre-event signups |
| Check-in Speed | <30 seconds average | Time from arrival to checked-in |
| Admin Time Savings | 50% reduction | Hours spent on coordination |
| Member Satisfaction | 4.5/5 stars | Post-event surveys |

#### Phase 2: Scale (6-12 Months)
**Goal**: Expand to 5-10 churches, validate multi-church model

| Metric | Target | Measurement |
|--------|--------|-------------|
| Church Adoption | 10 churches | Active church accounts |
| Monthly Active Users | 5,000+ | Users engaging weekly |
| Kiosk Interaction Rate | 60% of attendees | Kiosk check-ins vs total |
| Voice Recognition Accuracy | 90%+ | Successful voice commands |
| Notification Delivery Rate | 95%+ | Messages delivered successfully |

#### Phase 3: SaaS (12+ Months)
**Goal**: Become profitable SaaS with 50+ churches

| Metric | Target | Measurement |
|--------|--------|-------------|
| ARR (Annual Recurring Revenue) | $50,000+ | Subscription revenue |
| Churn Rate | <10% | Churches canceling |
| Net Promoter Score (NPS) | 50+ | Recommendation likelihood |
| Feature Usage | 75%+ active use | Core features used monthly |

### Leading Indicators

- **Week 1**: 50% of members install app
- **Week 2**: 70% have registered for first bus
- **Week 4**: Average response time to notifications <5 minutes
- **Month 3**: Admin time savings feedback: "couldn't go back"

---

## Functional Requirements

### 1. Authentication & User Management

#### 1.1 User Registration & Login
**Priority**: P0 (Must-Have for MVP)

**Requirements**:
- Phone number + OTP authentication via Supabase
- Branch selection during onboarding
- Profile creation (name, branch, volunteer roles, profile photo)
- Phone number validation with `phonenumbers` library
- Support for Ghanaian phone formats (+233)

**User Flow**:
```
1. Enter phone number → 2. Receive OTP via SMS → 3. Enter OTP →
4. Select branch → 5. Complete profile → 6. Access app
```

**Technical Notes**:
- Use Supabase Auth for OTP delivery
- Store user profiles in MongoDB
- JWT tokens for session management
- Auto-logout after 30 days of inactivity

#### 1.2 Role-Based Access Control (RBAC)
**Priority**: P0

**Roles**:
| Role | Permissions |
|------|-------------|
| **Member** | View events, register for buses/conferences, receive notifications |
| **Branch Admin** | Manage branch members, view branch analytics, assign volunteer roles |
| **Transport Coordinator** | Create bus routes, send delay notifications, check in passengers |
| **Conference Admin** | Create conferences, manage speakers, check in attendees |
| **Super Admin** | Full system access, manage all branches, configure system settings |

**Technical Implementation**:
- Role stored as array in User model: `roles: ['member', 'transport_coordinator']`
- FastAPI dependency injection for permission checks
- Frontend role-based navigation hiding/showing

---

### 2. Bus Transportation Coordination

#### 2.1 Bus Route Management
**Priority**: P0

**Requirements**:
- Create bus routes with pickup location, time, capacity, driver info
- Visual map integration (Google Maps API) for pickup points
- Auto-assignment when bus reaches capacity
- Waitlist management with notifications when spots open
- Bus status updates (scheduled, delayed, departed, arrived, cancelled)

**Data Model**:
```python
BusRoute:
  - name: str  # "Legon Bus #1"
  - pickup_location: str
  - pickup_coordinates: GeoJSON Point
  - departure_time: datetime
  - capacity: int
  - registered_count: int  # Calculated field
  - conference_id: ObjectId
  - driver_name: str
  - driver_phone: str
  - status: Enum["scheduled", "delayed", "departed", "arrived", "cancelled"]
  - delay_minutes: int (optional)
  - created_by: ObjectId (ref: User)
```

**Business Rules**:
- When `registered_count >= capacity`, auto-assign new registrations to next available bus for same pickup location
- Notify users when moved to different bus
- Transport coordinators can override auto-assignment
- Can't delete bus route with registered members

#### 2.2 Member Bus Registration
**Priority**: P0

**Requirements**:
- Browse available buses by conference and pickup location
- Filter by departure time, proximity, availability
- One-tap registration with confirmation
- QR code generation for boarding pass
- Cancel registration (up to 2 hours before departure)
- View "My Routes" with real-time status updates

**User Flow**:
```
1. Select conference → 2. Choose pickup location (dropdown or map) →
3. See available buses with capacity → 4. Select bus →
5. Confirm registration → 6. Receive QR code + push notification
```

#### 2.3 Real-Time Bus Updates & Notifications
**Priority**: P0

**Requirements**:
- Transport coordinators can send updates (delay, cancellation, gate change)
- Notifications sent only to registered members on that specific bus
- Multi-channel notification routing based on urgency:
  - **Urgent delays (30+ min)**: SMS + Push + WhatsApp
  - **Moderate delays (15-30 min)**: SMS + Push
  - **Minor delays (<15 min)**: Push only
  - **General updates**: Push + Email

**Technical Implementation**:
- Use `@apps/shared/integration/n8n.py` for workflow orchestration
- WebSocket connections for real-time updates in app
- Geo-filtering: Only notify users within 50km of pickup point (optional enhancement)

**Notification Templates** (stored in MongoDB):
```python
templates = {
    "bus_delay": "Bus {bus_name} delayed by {delay_minutes} minutes. New ETA: {new_time}. Pickup location: {location}. Sorry for the inconvenience!",
    "bus_departure": "Bus {bus_name} is now departing from {location}. Safe travels!",
    "bus_cancellation": "Unfortunately, Bus {bus_name} has been cancelled. We've moved you to {new_bus_name} departing at {new_time}."
}
```

---

### 3. Conference Registration & Management

#### 3.1 Conference Creation
**Priority**: P0

**Requirements**:
- Conference admins can create events with rich details
- Upload banner images, venue photos
- Add multiple speakers with bios and photos
- Create session schedules with times and descriptions
- Set registration limits and deadlines
- Publish/unpublish conferences

**Data Model**:
```python
Conference:
  - name: str
  - description: str (rich text)
  - start_date: datetime
  - end_date: datetime
  - venue: str
  - venue_coordinates: GeoJSON Point
  - banner_image_url: str  # Supabase Storage
  - registration_open: bool
  - max_capacity: int (optional)
  - registration_deadline: datetime (optional)
  - created_by: ObjectId (ref: User)
  - published: bool

Speaker:
  - conference_id: ObjectId (ref: Conference)
  - name: str
  - title: str  # "Pastor", "Bishop", "Guest Speaker"
  - bio: str
  - photo_url: str  # Supabase Storage
  - session_topic: str (optional)
  - session_time: datetime (optional)
  - order: int  # Display order

Session:
  - conference_id: ObjectId (ref: Conference)
  - title: str
  - description: str
  - start_time: datetime
  - end_time: datetime
  - location: str  # "Main Auditorium", "Hall A"
  - speaker_ids: List[ObjectId]
```

#### 3.2 Member Conference Registration
**Priority**: P0

**Requirements**:
- Browse upcoming conferences
- View conference details, speakers, schedule
- One-tap registration
- Automatic QR code generation for check-in
- Add to calendar integration (Google Calendar, Apple Calendar)
- Share conference details via WhatsApp/SMS
- Cancel registration (up to event start)

**User Flow**:
```
1. See conference banner on home screen → 2. Tap to view details →
3. Review speakers & schedule → 4. Tap "Register" →
5. Receive QR code → 6. Get reminder notifications (7 days, 3 days, 1 day, 3 hours before)
```

#### 3.3 Check-In System
**Priority**: P0

**Requirements**:
- Multiple check-in methods:
  - **QR Code Scan** - Fastest, primary method
  - **Phone Number Lookup** - Backup if QR not working
  - **Voice AI Kiosk** - Hands-free, personalized (Phase 2)
  - **Manual Entry** - Admin override
- Check-in confirmation with welcome message
- Track check-in time and method
- Real-time attendance dashboard for admins
- Check-in analytics (on-time rate, method breakdown)

**Business Rules**:
- Can only check in once per conference
- Check-in opens 2 hours before event start
- Late check-ins allowed but flagged
- No check-in after event ends (configurable)

---

### 4. AI Voice Kiosk "Ama" (Phase 2)

#### 4.1 Voice AI Assistant Persona
**Priority**: P1 (Phase 2)

**Ama's Characteristics**:
- **Name**: Ama (Ghanaian name meaning "born on Saturday")
- **Personality**: Warm, respectful, joyful, culturally aware
- **Voice**: Female Ghanaian-accented English (via Coqui XTTS + Voice Lab)
- **Languages**: English (primary), Twi greetings and expressions
- **Knowledge**: Member names, branches, volunteer roles, attendance history, bus info

**Technical Implementation**:
- Use `@apps/shared/integration/vapi.py` for conversational AI
- Use `@apps/shared/integration/rag.py` with Gemini 2.5 Flash for context retrieval
- Store member interaction history in MongoDB for personalization
- Text-to-speech via `@apps/shared/integration/ai_services/` (Coqui XTTS or MeloTTS)

#### 4.2 Personalized Greeting System
**Priority**: P1

**Requirements**:
- Motion detection triggers greeting (camera + MediaPipe or PIR sensor)
- Voice input for name capture
- Database lookup with fuzzy matching
- Generate personalized greeting based on:
  - **Attendance pattern** - "Always a joy to see you!" vs "Welcome back!"
  - **Volunteer role** - "Thank you for serving in the choir"
  - **Bus registration** - "Your bus departs at 5:30 PM from Gate 3"
  - **Branch** - "Hi Akosua from Legon branch!"
- Display greeting text on screen while speaking
- Check-in integration (optional voice confirmation)

**Greeting Template System**:
```python
greeting_parts = [
    f"Hi {name} from {branch} branch!",  # Always included
    attendance_comment,  # Based on history
    volunteer_role_comment,  # If user has role
    bus_info,  # If registered for bus
]

# Example output:
# "Hi Akosua from Legon branch! It's always a joy to see you here.
#  Thank you for serving in the choir — your ministry is such a blessing.
#  Your bus departs at 5:30 PM from Gate 3. Can I check you in?"
```

**Conversation Flow**:
```
1. Motion detected → Display welcome animation
2. Ama: "Akwaaba! Welcome to Impact 2025. What's your name, please?"
3. User: [Speaks name] → Voice-to-text via Whisper
4. System: Database lookup → Find member
5. Ama: [Personalized greeting based on member data]
6. Ama: "Can I check you in?"
7. User: "Yes" → Check-in complete → Display QR code
8. Ama: "You're all set! Have a wonderful time!"
```

**Fallback Mechanisms**:
- If voice recognition fails → Show on-screen keyboard
- If no database match → "Nice to meet you! Let's get you registered."
- If system error → "Please visit the help desk for assistance."

#### 4.3 RAG-Powered Context Awareness
**Priority**: P1

**Requirements**:
- Use `@apps/shared/integration/rag.py` with Gemini 2.5 Flash for semantic search
- Ingest member profiles, volunteer roles, attendance history into vector DB (Supabase pgvector)
- Real-time context retrieval during interactions
- Query: "Who is this person and what should I know about them?"
- Response includes: name, branch, roles, last 5 events attended, special notes

**Technical Implementation**:
```python
from apps.shared.integration.rag import RAGService

rag = RAGService(
    collection_name="churchflow_members",
    provider="gemini",  # Gemini 2.5 Flash
    model_name="gemini-2.5-flash"
)

# When member says name
query = f"Find member named {user_input_name} from branch {branch_name}"
results = await rag.query(
    query=query,
    top_k=3,
    min_similarity=0.75
)

# Extract member data
member = results[0].metadata  # Contains full profile
greeting = generate_personalized_greeting(member)
```

**Vector Embeddings Strategy**:
- Embed member profiles as: `"{name} from {branch}, serves as {role}, attended {event_list}"`
- Update embeddings after each event attendance
- Use semantic search for fuzzy name matching ("Akosua" → "Akosua Mensah", "Akua", etc.)

---

### 5. Intelligent Notification System

#### 5.1 Multi-Channel Notification Routing
**Priority**: P0

**Requirements**:
- Orchestrated via `@apps/shared/integration/n8n.py` workflows
- Channel selection based on urgency and message type:

| Message Type | Urgency | Channels | Rationale |
|--------------|---------|----------|-----------|
| Bus delay (30+ min) | Critical | SMS + Push + WhatsApp | Affects travel plans, must reach immediately |
| Bus delay (15-30 min) | High | SMS + Push | Important but less critical |
| Bus delay (<15 min) | Medium | Push | Minor inconvenience |
| Conference reminder (1 day) | Medium | Push + Email | Advance notice |
| Conference reminder (3 hours) | High | SMS + Push | Timely reminder |
| Check-in confirmation | Low | Push + Email | Receipt, not urgent |
| General announcement | Low | Push | Informational |

**Technical Implementation**:
```python
from apps.shared.integration.n8n import N8NIntegration

n8n = N8NIntegration()

# Create notification workflow
workflow_id = await n8n.create_workflow(
    name="Bus Delay Notification - Multi-Channel",
    trigger={"type": "webhook", "path": "bus-delay"},
    nodes=[
        {
            "type": "switch",
            "condition": "delay_minutes >= 30",
            "branches": ["sms", "push", "whatsapp"]
        },
        {
            "type": "twilio_sms",
            "message": "Bus {{bus_name}} delayed {{delay_minutes}} min. New ETA: {{new_time}}"
        },
        {
            "type": "firebase_push",
            "title": "Bus Delay",
            "body": "Your bus is delayed. Tap for details."
        },
        {
            "type": "twilio_whatsapp",
            "message": "🚌 Bus Update: {{bus_name}} delayed..."
        }
    ]
)

# Trigger workflow
await n8n.execute_workflow(
    workflow_id=workflow_id,
    data={
        "user_id": str(user.id),
        "phone": user.phone,
        "fcm_token": user.fcm_token,
        "delay_minutes": 45,
        "bus_name": "Legon Bus #1",
        "new_time": "5:45 PM"
    }
)
```

#### 5.2 Scheduled Conference Reminders
**Priority**: P0

**Requirements**:
- Automated reminders at: 7 days, 3 days, 1 day, 3 hours before event
- Personalized with conference name, time, user's bus info (if registered)
- Opt-out option in app settings
- Retry logic for failed deliveries
- Delivery receipts logged in MongoDB

**Technical Implementation**:
- n8n scheduled workflows with cron triggers
- Check registration status before sending
- Include "Add to Calendar" link in email notifications
- Deep link to conference details in push notifications

#### 5.3 Notification Preferences
**Priority**: P1

**Requirements**:
- User settings for notification frequency
- Per-channel opt-in/opt-out (can't disable SMS for critical alerts)
- Quiet hours (no push notifications 10 PM - 6 AM unless critical)
- Notification history in app
- Mark as read/unread
- Delete notifications

---

### 6. Admin Dashboard (Web Interface)

#### 6.1 Transport Coordinator Dashboard
**Priority**: P0

**Requirements**:
- **Bus Route Management**:
  - Create, edit, delete bus routes
  - Visual capacity indicators (75% full = yellow, 100% = red)
  - Real-time registration list per bus
  - Export passenger manifest (PDF, Excel)

- **Live Updates Panel**:
  - Send delay notifications with one tap
  - Update bus status (departed, arrived, cancelled)
  - View notification delivery status

- **Check-In Interface**:
  - QR code scanner (webcam or mobile)
  - Phone number search
  - Mark passengers as checked in
  - Late arrivals flagged

**UI Components**:
- Bus capacity bar charts
- Map view of pickup locations
- Passenger list with search/filter
- Quick actions: "Send Delay Notice", "Mark as Departed"

#### 6.2 Conference Admin Dashboard
**Priority**: P0

**Requirements**:
- **Conference Management**:
  - Create/edit conferences with rich editor
  - Upload images (drag & drop to Supabase Storage)
  - Manage speakers and sessions
  - Set registration limits and deadlines

- **Registration Overview**:
  - Real-time registration count
  - Demographic breakdown (by branch, age group if available)
  - Check-in status (pending, checked-in, no-show)
  - Export attendee list

- **Check-In Interface**:
  - QR scanner for rapid check-in
  - Search by name or phone
  - Manual check-in override
  - Real-time attendance counter

#### 6.3 Super Admin Dashboard
**Priority**: P1 (Phase 2)

**Requirements**:
- **User Management**:
  - View all users, filter by branch/role
  - Assign/revoke roles
  - Deactivate accounts

- **Branch Management**:
  - Create, edit branches
  - Set branch admins
  - View branch-level analytics

- **System Configuration**:
  - Notification template editor
  - Kiosk settings (motion sensitivity, voice volume)
  - Feature flags (enable/disable modules)

- **Analytics Dashboard**:
  - Total users, active users (7-day, 30-day)
  - Event attendance trends (line chart)
  - Bus utilization rate
  - Top branches by engagement
  - Notification delivery metrics
  - Export reports (PDF, CSV)

---

### 7. Mobile App Experience

#### 7.1 Onboarding Flow
**Priority**: P0

**Screens**:
1. **Welcome Screen** - App logo, tagline, "Get Started" CTA
2. **Phone Entry** - "Enter your phone number" with country code
3. **OTP Verification** - 6-digit code input, "Resend Code" link
4. **Branch Selection** - Searchable dropdown of branches
5. **Profile Setup** - Name, optional profile photo, volunteer roles (multi-select)
6. **Permissions** - Request push notification permissions
7. **Home Screen** - "You're all set!" with onboarding tour overlay

#### 7.2 Home Screen
**Priority**: P0

**Layout** (Mobile-First, Vertical Scroll):
```
┌─────────────────────────────────┐
│  [Profile Icon]  ChurchFlow  🔔 │  ← Header with notifications bell
├─────────────────────────────────┤
│                                 │
│  🎪 Conference Card             │  ← Banner with image
│  Impact 2025                    │     Tap → Conference details
│  Dec 20-22, 2025                │
│  [Register Now] or [Registered✓]│
│                                 │
├─────────────────────────────────┤
│  🚌 My Bus                      │  ← Conditional: only if registered
│  Legon Bus #1                   │
│  Departs: 5:30 PM from Gate 3   │
│  Status: On Time ✅             │
│  [View Details]                 │
├─────────────────────────────────┤
│  Quick Actions                  │
│  [🎫 Check-In] [🚌 My Routes]  │
│  [📅 Events]   [👤 Profile]    │
├─────────────────────────────────┤
│  📢 Recent Notifications        │
│  • Bus #1 departure reminder    │
│  • New speaker added to Impact  │
│  [View All]                     │
├─────────────────────────────────┤
│  Upcoming Events                │
│  • Impact 2025 - Dec 20         │
│  • Youth Retreat - Jan 15       │
└─────────────────────────────────┘
```

**Interactions**:
- Pull-to-refresh for latest updates
- Swipe left on notification to delete
- Tap conference card → Conference details
- Tap bus card → Bus route details with real-time status

#### 7.3 Bus Registration Flow
**Priority**: P0

**Screens**:
1. **Conference Selection** - List of upcoming conferences
2. **Pickup Location** - Map view + list of pickup points, sorted by proximity
3. **Available Buses** - Cards showing bus name, time, capacity bar, driver
4. **Confirm Registration** - Summary with "Confirm" CTA
5. **Success Screen** - QR code, save to wallet, share button

**UI Details**:
- Capacity indicator: Green (<75%), Yellow (75-95%), Red (95-100%)
- Distance to pickup point: "2.3 km from you"
- Estimated travel time: "30 min journey"

#### 7.4 Conference Details Screen
**Priority**: P0

**Layout**:
```
┌─────────────────────────────────┐
│  ← Back         Impact 2025  ⋮  │  ← Options menu
├─────────────────────────────────┤
│  [Conference Banner Image]      │
│                                 │
│  Impact 2025                    │
│  December 20-22, 2025           │
│  📍 National Theatre, Accra     │
│  👥 1,234 registered            │
│                                 │
│  [Register Now] [Share]         │
├─────────────────────────────────┤
│  📋 Tabs: [Details] [Speakers]  │
│           [Schedule] [My QR]    │
├─────────────────────────────────┤
│  About                          │
│  [Conference description...]    │
│                                 │
│  What to Bring                  │
│  • Bible • Notebook • ID        │
│                                 │
│  [View on Map]                  │
└─────────────────────────────────┘
```

#### 7.5 Notifications Tab
**Priority**: P0

**Features**:
- Grouped by date (Today, Yesterday, This Week, Older)
- Filter by type (All, Bus, Conference, Announcements)
- Mark all as read
- Swipe to delete
- Deep links to relevant screens

---

## Technical Architecture

### System Overview

```
┌────────────────────────────────────────────────┐
│              Users (Mobile + Kiosk)            │
└───────────────┬────────────────────────────────┘
                │ HTTPS
                ▼
┌────────────────────────────────────────────────┐
│          Nginx Reverse Proxy                   │
│     church.kasaai.ailabsafrica.com             │
└───────────────┬────────────────────────────────┘
                │
                ▼
┌────────────────────────────────────────────────┐
│        FastAPI Backend (Python 3.11+)          │
│    - REST API endpoints                        │
│    - WebSocket server (real-time updates)      │
│    - Business logic services                   │
└──┬──────┬──────┬──────┬──────┬─────────────────┘
   │      │      │      │      │
   ▼      ▼      ▼      ▼      ▼
┌──────┐ ┌───┐ ┌─────┐ ┌────┐ ┌────────────────┐
│Mongo │ │n8n│ │VAPI │ │RAG │ │AI Services     │
│DB    │ │   │ │     │ │(Ge-│ │(TTS/LLM/ASR)   │
│      │ │   │ │     │ │mini│ │                │
└──────┘ └───┘ └─────┘ └────┘ └────────────────┘
```

### Technology Stack

#### Backend
- **Framework**: FastAPI 0.115+
- **Language**: Python 3.11+
- **Database**: MongoDB 7.0+ (Motor async driver)
- **Auth**: Supabase Auth (PostgreSQL + JWT)
- **Vector DB**: Supabase pgvector (for RAG embeddings)
- **Async**: asyncio, aiohttp
- **Validation**: Pydantic 2.0+

#### Frontend (Mobile)
- **Framework**: React Native (Expo)
- **Language**: TypeScript
- **State**: React Context API + Hooks
- **Navigation**: React Navigation 6
- **Notifications**: Firebase Cloud Messaging
- **Storage**: AsyncStorage (encrypted)
- **API Client**: Axios

#### Frontend (Kiosk & Admin)
- **Framework**: React 18
- **Build**: Vite
- **Language**: TypeScript
- **Styling**: Tailwind CSS
- **Components**: shadcn/ui
- **Voice**: Browser Web Speech API + VAPI SDK

#### Shared Services (from `@apps/shared/integration/`)
- **VAPI** (`vapi.py`) - Voice AI, phone calls
- **n8n** (`n8n.py`) - Notification workflows
- **RAG** (`rag.py`) - Semantic search with Gemini 2.5 Flash
- **AI Services** (`ai_services/`) - TTS/LLM/ASR management
- **Wallet** (`wallet.py`) - Usage tracking
- **Document Processor** (`document_processor.py`) - PDF/DOCX parsing

#### Infrastructure
- **Reverse Proxy**: Nginx
- **Process Manager**: Systemd
- **AI Hosting**: Self-hosted (Ollama, Coqui, Whisper)
- **SSL**: Let's Encrypt
- **Monitoring**: Sentry (errors), custom health checks

### Data Architecture

#### MongoDB Collections

```python
# Users
{
    "_id": ObjectId,
    "phone": "+233201234567",  # Indexed, unique
    "name": "Akosua Mensah",
    "branch_id": ObjectId,  # Indexed
    "roles": ["member", "usher"],
    "volunteer_roles": ["usher", "choir"],
    "profile_image_url": "https://...",
    "fcm_token": "...",  # Push notifications
    "notification_preferences": {
        "sms": true,
        "push": true,
        "whatsapp": true,
        "email": true,
        "quiet_hours": {"start": "22:00", "end": "06:00"}
    },
    "created_at": ISODate,
    "last_active": ISODate
}

# Branches
{
    "_id": ObjectId,
    "name": "Legon Branch",
    "location": {"type": "Point", "coordinates": [-0.1870, 5.6484]},  # GeoJSON
    "contact_person": "Pastor Mensah",
    "contact_phone": "+233501234567"
}

# Conferences
{
    "_id": ObjectId,
    "name": "Impact 2025",
    "description": "...",
    "start_date": ISODate,
    "end_date": ISODate,
    "venue": "National Theatre",
    "venue_coordinates": {"type": "Point", "coordinates": [...]},
    "banner_image_url": "https://...",
    "registration_open": true,
    "max_capacity": 5000,
    "created_by": ObjectId,  # User ID
    "created_at": ISODate
}

# BusRoutes
{
    "_id": ObjectId,
    "name": "Legon Bus #1",
    "pickup_location": "Legon Mall",
    "pickup_coordinates": {"type": "Point", "coordinates": [...]},  # Indexed for geo queries
    "departure_time": ISODate,
    "capacity": 50,
    "conference_id": ObjectId,  # Indexed
    "driver_name": "Kwame Asante",
    "driver_phone": "+233201234567",
    "status": "scheduled",  # Enum: scheduled, delayed, departed, arrived, cancelled
    "delay_minutes": 0,
    "created_at": ISODate
}

# BusRegistrations
{
    "_id": ObjectId,
    "user_id": ObjectId,  # Indexed
    "bus_route_id": ObjectId,  # Indexed
    "conference_id": ObjectId,
    "registration_status": "confirmed",  # confirmed, waitlisted, cancelled
    "seat_number": 12,
    "checked_in": false,
    "checked_in_at": null,
    "qr_code": "CR-ABC123",  # Unique, indexed
    "created_at": ISODate
}

# ConferenceRegistrations
{
    "_id": ObjectId,
    "user_id": ObjectId,  # Compound index: (user_id, conference_id)
    "conference_id": ObjectId,
    "registration_date": ISODate,
    "checked_in": false,
    "check_in_time": null,
    "check_in_method": null,  # qr_code, phone, kiosk, manual
    "qr_code": "CF-XYZ789"  # Unique, indexed
}

# NotificationLogs
{
    "_id": ObjectId,
    "user_id": ObjectId,  # Indexed
    "template_type": "bus_delay",
    "channel": "sms",  # sms, push, whatsapp, email
    "message": "Bus Legon #1 delayed...",
    "sent_at": ISODate,
    "delivered": true,
    "delivered_at": ISODate,
    "error_message": null
}
```

#### Supabase PostgreSQL (via pgvector for RAG)

```sql
-- Member embeddings for RAG-powered search
CREATE TABLE churchflow_member_embeddings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id TEXT NOT NULL,  -- MongoDB user _id as string
    content TEXT NOT NULL,  -- Full member profile text
    embedding VECTOR(1536),  -- Gemini 2.5 Flash embeddings
    metadata JSONB,  -- {name, branch, roles, attendance_count, ...}
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX ON churchflow_member_embeddings USING ivfflat (embedding vector_cosine_ops);
CREATE INDEX ON churchflow_member_embeddings (user_id);
```

### API Endpoints

#### Authentication
```
POST   /api/v1/auth/send-otp          # Send OTP to phone
POST   /api/v1/auth/verify-otp        # Verify OTP and return JWT
POST   /api/v1/auth/refresh           # Refresh access token
```

#### Users
```
GET    /api/v1/users/me               # Get current user
PUT    /api/v1/users/me               # Update current user
PUT    /api/v1/users/me/photo         # Upload profile photo
GET    /api/v1/users/{id}             # Get user by ID (admin)
```

#### Conferences
```
GET    /api/v1/conferences            # List conferences
GET    /api/v1/conferences/{id}       # Get conference details
POST   /api/v1/conferences            # Create conference (admin)
PUT    /api/v1/conferences/{id}       # Update conference (admin)
POST   /api/v1/conferences/{id}/register  # Register for conference
GET    /api/v1/conferences/{id}/speakers  # Get speakers
POST   /api/v1/conferences/{id}/check-in  # Check in user
```

#### Buses
```
GET    /api/v1/buses/routes           # List bus routes (filterable)
GET    /api/v1/buses/routes/{id}      # Get bus route details
POST   /api/v1/buses/register         # Register for bus
DELETE /api/v1/buses/register/{id}    # Cancel bus registration
GET    /api/v1/buses/my-routes        # User's registered buses
POST   /api/v1/buses/routes           # Create route (coordinator)
PUT    /api/v1/buses/routes/{id}      # Update route (coordinator)
POST   /api/v1/buses/updates          # Send bus update (coordinator)
POST   /api/v1/buses/check-in         # Check in passenger
```

#### Kiosk (AI Voice)
```
POST   /api/v1/kiosk/search-user      # Search by name + branch
POST   /api/v1/kiosk/greeting         # Generate personalized greeting
POST   /api/v1/kiosk/check-in         # Voice check-in
GET    /api/v1/kiosk/member-context/{user_id}  # RAG-powered context
```

#### Notifications
```
POST   /api/v1/notifications/send     # Send notification (admin)
GET    /api/v1/notifications/history  # User's notification history
PUT    /api/v1/notifications/preferences  # Update preferences
```

#### WebSocket
```
WS     /api/v1/ws/{user_id}           # Real-time updates stream
```

### Integration with Shared Services

#### VAPI Integration (Voice AI for Phone Calls)
```python
from apps.shared.integration.vapi import VAPIIntegration

vapi = VAPIIntegration()

# Create AI assistant for phone surveys
assistant = await vapi.create_assistant(
    name="ChurchFlow Survey Assistant",
    system_prompt="You are calling to gather feedback about our recent conference...",
    voice="jennifer",
    first_message="Hi, this is Ama from ChurchFlow. Do you have a moment for a quick survey?",
    functions=[
        {
            "name": "record_feedback",
            "description": "Record user feedback in database",
            "parameters": {
                "type": "object",
                "properties": {
                    "rating": {"type": "number"},
                    "comments": {"type": "string"}
                }
            }
        }
    ]
)

# Make outbound call to member
call = await vapi.create_call(
    assistant_id=assistant.id,
    customer_phone="+233201234567",
    metadata={"user_id": str(user.id), "conference_id": str(conf.id)}
)
```

#### RAG Integration (Gemini 2.5 Flash)
```python
from apps.shared.integration.rag import RAGService

rag = RAGService(
    collection_name="churchflow_members",
    provider="gemini",
    model_name="gemini-2.5-flash",
    embedding_dimension=1536
)

# Ingest member profile for semantic search
await rag.ingest_document(
    content=f"{user.name} from {user.branch_name}, serves as {', '.join(user.volunteer_roles)}",
    metadata={
        "user_id": str(user.id),
        "name": user.name,
        "branch": user.branch_name,
        "roles": user.volunteer_roles,
        "attendance_count": user.attendance_count
    }
)

# Query during kiosk interaction
query = f"Who is {user_voice_input} from {branch_input}?"
results = await rag.query(query, top_k=3, min_similarity=0.75)

if results:
    member = results[0].metadata
    greeting = generate_personalized_greeting(member)
```

#### n8n Workflow Integration (Multi-Channel Notifications)
```python
from apps.shared.integration.n8n import N8NIntegration

n8n = N8NIntegration()

# Trigger bus delay notification workflow
await n8n.execute_workflow_webhook(
    workflow_name="bus-delay-notification",
    data={
        "recipients": [{"phone": u.phone, "fcm_token": u.fcm_token} for u in users],
        "delay_minutes": 30,
        "bus_name": "Legon Bus #1",
        "new_eta": "6:00 PM"
    }
)
```

#### AI Services Integration (TTS for Kiosk)
```python
from apps.shared.integration.ai_services import AIProviderService, ProviderType

tts_service = AIProviderService(provider_type=ProviderType.TTS)

# Generate speech for personalized greeting
audio_response = await tts_service.request(
    provider_name="coqui_xtts",
    text=greeting_text,
    parameters={
        "language": "en",
        "voice": "female_ghanaian",
        "speed": 1.0
    }
)

# Play audio on kiosk speakers
await play_audio(audio_response.audio_data)
```

---

## User Experience & Design

### Design Principles

1. **Mobile-First** - Optimize for small screens, then scale up
2. **One-Handed Use** - Primary actions reachable with thumb
3. **Clear Hierarchy** - Important info big, secondary info smaller
4. **High Contrast** - Readable in bright sunlight
5. **Generous Touch Targets** - Minimum 44×44 pts
6. **Offline Resilience** - Cache data, queue actions
7. **Fast Feedback** - Loading states, success animations
8. **Accessibility** - Screen reader support, high contrast mode

### Visual Design

#### Color Palette
```
Primary (Purple):     #7C3AED (Deep Purple)
Secondary (Teal):     #14B8A6 (Teal 500)
Success (Green):      #10B981 (Emerald 500)
Warning (Yellow):     #F59E0B (Amber 500)
Error (Red):          #EF4444 (Red 500)
Background (Light):   #F9FAFB (Gray 50)
Surface (White):      #FFFFFF
Text (Dark):          #111827 (Gray 900)
Text (Light):         #6B7280 (Gray 500)
```

#### Typography
```
Headings:   SF Pro Display / Roboto (700 Bold)
Body:       SF Pro Text / Roboto (400 Regular)
Labels:     SF Pro Text / Roboto (500 Medium)
```

#### Spacing
```
xs:  4px    (Tight spacing)
sm:  8px    (Small gaps)
md:  16px   (Standard spacing)
lg:  24px   (Section separators)
xl:  32px   (Screen padding)
2xl: 48px   (Major sections)
```

### Key Screens (Mobile)

#### Home Screen
- Bright conference banner (hero image)
- Subtle shadow on cards
- Green checkmark for completed actions
- Skeleton loaders while fetching data

#### Bus Registration
- Map view with custom purple markers
- Capacity bar with color coding (green/yellow/red)
- Floating "Confirm" button at bottom
- Success animation (confetti) on registration

#### Check-In Flow
- Large, centered QR code
- "Save to Wallet" button (Apple Wallet / Google Pay)
- Countdown timer until event start
- Tap QR to enlarge (full screen)

#### Kiosk Interface
- **Idle State**: Looping video background, "Tap to Start"
- **Active State**: Large text, animated speaking avatar (optional)
- **Success**: Green checkmark animation, QR code display
- **Error**: Friendly error message, "Call for Help" button

### Animation & Interaction

#### Micro-Interactions
- Button press: Scale down 0.95x + subtle shadow
- Pull-to-refresh: Elastic bounce animation
- Notification badge: Pulse animation on new message
- Check-in success: Confetti explosion + haptic feedback

#### Transitions
- Screen navigation: Slide from right (iOS) / Fade (Android)
- Modal appearance: Scale up from 0.9x + fade in
- Card expansion: Smooth height transition (300ms ease-out)

---

## Security & Privacy

### Data Protection

#### Encryption
- **At Rest**: MongoDB encryption at rest
- **In Transit**: TLS 1.3 for all API calls
- **Sensitive Fields**: Encrypt phone numbers with AES-256
- **JWT Tokens**: HS256 signing, 24-hour expiry

#### Authentication Security
- **OTP**: 6-digit code, 5-minute expiry, max 3 attempts
- **Password (Admin)**: Bcrypt hashing, min 12 characters
- **Session Management**: Refresh tokens (30 days), access tokens (24 hours)
- **Rate Limiting**: 5 OTP requests per phone per hour

#### Authorization
- Role-based access control (RBAC)
- API endpoints protected with JWT verification
- Admin actions require additional permission check
- Audit logs for sensitive operations (user role changes, deletions)

### Privacy Compliance

#### Data Minimization
- Only collect: name, phone, branch, volunteer roles
- No: email (optional), address, birthdate, financial info
- Voice recordings NOT stored (real-time only)

#### User Rights (GDPR-Style)
- **Access**: Users can export their data (JSON)
- **Rectification**: Users can edit their profiles
- **Erasure**: Users can delete accounts (soft delete, 30-day grace)
- **Portability**: Export includes all events, registrations, notifications

#### Consent Management
- Explicit opt-in for notifications during onboarding
- Clear privacy policy link in app footer
- Kiosk displays: "Voice interactions not recorded" notice

### Security Best Practices

#### API Security
- CORS: Whitelist only known domains
- Rate Limiting: 100 requests/min per user
- Input Validation: Pydantic models, SQL injection prevention
- Error Messages: Generic errors, no stack traces in production

#### Infrastructure
- Regular security updates (monthly patch cycle)
- Firewall: Only ports 80, 443, 22 (SSH) open
- SSH: Key-based auth only, no password login
- Secrets: Stored in `.env`, never in code

---

## Integration Points

### External Services

#### Supabase (Authentication & Storage)
- **Auth**: Phone OTP, JWT generation
- **Storage**: Profile photos, conference banners, speaker photos
- **pgvector**: RAG embeddings for member search

#### Twilio (SMS & WhatsApp)
- SMS for critical bus delay notifications
- WhatsApp for rich media (event schedules, maps)
- Delivery receipts tracked in MongoDB

#### Firebase Cloud Messaging (Push Notifications)
- Cross-platform (iOS + Android)
- Topic-based notifications (e.g., "conference-impact-2025")
- Delivery analytics

#### SendGrid (Email)
- Conference registration confirmations
- Monthly engagement reports for admins
- HTML email templates

#### Google Maps API
- Display pickup locations on map
- Calculate distance to user
- Generate shareable location links

### Internal Shared Services

#### AI Services (`@apps/shared/integration/ai_services/`)
- **TTS**: Coqui XTTS (English & Twi), MeloTTS, F5-TTS
- **LLM**: Ollama (Llama 3.2, Gemini 2.5 Flash via OpenRouter)
- **ASR**: Akan Whisper (Twi), Whisper Large v3 (English)

#### VAPI (`@apps/shared/integration/vapi.py`)
- Voice AI phone calls for surveys
- Kiosk conversational interface
- Real-time transcription

#### n8n (`@apps/shared/integration/n8n.py`)
- Notification workflow orchestration
- Multi-channel routing logic
- Scheduled reminders

#### RAG (`@apps/shared/integration/rag.py`)
- Semantic member search
- Context retrieval for Ama
- Gemini 2.5 Flash embeddings

#### Wallet (`@apps/shared/integration/wallet.py`)
- Track AI service usage (TTS/LLM calls)
- Cost calculation for potential billing (future SaaS)

---

## Release Strategy

### Phase 1: MVP (Months 1-6)
**Goal**: Validate core value with single church deployment

**Features**:
- ✅ Phone OTP authentication
- ✅ User profiles with branch assignment
- ✅ Bus route management (create, view, register)
- ✅ Conference management (create, view, register)
- ✅ QR code check-in
- ✅ Multi-channel notifications (SMS + Push)
- ✅ Mobile app (iOS + Android via Expo)
- ✅ Basic admin dashboard

**Launch Checklist**:
- [ ] 100+ beta users recruited
- [ ] Backend deployed to production
- [ ] Mobile app on TestFlight & Play Store Beta
- [ ] Admin training completed (2-hour workshop)
- [ ] Test event: 200-person gathering
- [ ] Feedback collection mechanism (in-app survey)

**Success Criteria**:
- 70% of members install app before first event
- 85% of bus riders register via app
- <30 sec average check-in time
- 4.5/5 star rating on post-event survey

### Phase 2: AI Kiosk & Scale (Months 7-12)
**Goal**: Deploy AI kiosk, expand to 5-10 churches

**Features**:
- ✅ AI Voice Assistant "Ama" (VAPI integration)
- ✅ RAG-powered personalized greetings (Gemini 2.5 Flash)
- ✅ Motion-detected kiosk interface
- ✅ Enhanced analytics dashboard
- ✅ Multi-church support (tenant isolation)
- ✅ White-label branding options

**Deployment Plan**:
- Month 7-8: Kiosk development & testing
- Month 9: Deploy kiosk at pilot church
- Month 10-12: Onboard 5 new churches (1-2 per month)

**Success Criteria**:
- 60% of attendees interact with kiosk
- 90%+ voice recognition accuracy
- 5 churches actively using platform
- Positive NPS (>30)

### Phase 3: SaaS Launch (Months 13-24)
**Goal**: Scale to 50+ churches, achieve profitability

**Features**:
- ✅ Subscription management (Stripe/Paystack)
- ✅ Self-service onboarding for new churches
- ✅ Advanced analytics (predictive attendance, engagement scoring)
- ✅ Volunteer management module
- ✅ Donation/payment integration (MoMo, Paystack)
- ✅ Mobile app white-labeling

**Pricing Model**:
```
Free Tier:        1 church, 500 members, 5 events/year
Starter:    ₵300/month - 1 church, 1000 members, unlimited events
Growth:     ₵500/month - 1 church, 2500 members, advanced analytics
Enterprise: ₵1500/month - Multi-church, unlimited, custom features
```

**Go-to-Market**:
- Partner with Ghana Pentecostal Council
- Sponsor church leadership conferences
- Offer 3-month free trial to first 100 churches
- Referral program: 1 month free for each new church referred

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Voice recognition fails in noisy venues | Medium | High | Fallback to on-screen keyboard; noise-canceling mics |
| SMS delivery failures during peak times | Medium | High | Retry logic; Push notification backup; Pre-send test messages |
| MongoDB performance bottlenecks at scale | Low | Medium | Implement indexes; Read replicas; Query optimization |
| Mobile app crashes on low-end devices | Medium | Medium | Extensive device testing; Performance profiling; Graceful degradation |
| Supabase Auth downtime | Low | High | Implement caching; Local fallback auth; Status page monitoring |

### Product Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Low user adoption (members don't install app) | Medium | High | In-church demos; QR code posters; SMS download links; Pastor endorsements |
| Admin resistance to new system | Medium | High | Extensive training; Gradual rollout; 24/7 support hotline |
| Feature creep delays MVP | High | Medium | Strict scope management; "Phase 2" parking lot; Weekly priority reviews |
| Competition from existing tools (WhatsApp groups) | Medium | Medium | Emphasize unique value (AI kiosk, smart routing); Show time savings |

### Business Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Churches unwilling to pay (post-free-tier) | Medium | High | Demonstrate ROI (time saved, increased attendance); Flexible pricing; Annual discounts |
| Key church staff turnover | Medium | Medium | Document processes; Multiple admin training; Video tutorials |
| Data privacy concerns | Low | High | Transparent privacy policy; No unnecessary data collection; Regular audits |
| Dependency on third-party APIs (Twilio, Supabase) | Low | Medium | Diversify providers; Monitor uptime; Budget for API costs |

### Mitigation Summary

**Top 3 Priorities**:
1. **User Adoption** → In-church marketing, pastor endorsements, easy onboarding
2. **Notification Reliability** → Multi-channel redundancy, delivery monitoring
3. **Voice AI Quality** → Extensive testing, fallback mechanisms, clear expectations

---

## Appendix

### Glossary

- **Ama**: AI voice assistant name (Ghanaian name meaning "born on Saturday")
- **Branch**: A local congregation within the larger church network
- **Check-in**: Process of confirming attendance at a conference/event
- **Conference**: Large church gathering/event (e.g., "Impact 2025")
- **Kiosk**: Tablet-based station with AI voice interface for check-in
- **OTP**: One-Time Password (6-digit code sent via SMS)
- **RAG**: Retrieval-Augmented Generation (AI technique for context-aware responses)
- **Transport Coordinator**: Role responsible for managing bus logistics

### Acronyms

- **API**: Application Programming Interface
- **ASR**: Automatic Speech Recognition
- **CTA**: Call to Action
- **FCM**: Firebase Cloud Messaging
- **JWT**: JSON Web Token
- **LLM**: Large Language Model
- **MVP**: Minimum Viable Product
- **NPS**: Net Promoter Score
- **OTP**: One-Time Password
- **PRD**: Product Requirements Document
- **QR**: Quick Response (code)
- **RAG**: Retrieval-Augmented Generation
- **RBAC**: Role-Based Access Control
- **SMS**: Short Message Service
- **TTS**: Text-to-Speech
- **UX**: User Experience
- **VAPI**: Voice API (Vapi.ai)

### References

- [ChurchFlow Architecture Strategy](/opt/kasaai/apps/ARCHITECTURE_STRATEGY.md)
- [ChurchFlow Planning Document](/opt/kasaai/apps/churchflow/PLANNING.md)
- [Ama AI Assistant Design](/opt/kasaai/apps/churchflow/docs/AMA_AI_ASSISTANT.md)
- [KasaAI Platform Architecture](/opt/kasaai/apps/architecture/ARCHITECTURE.md)
- [Shared Services Integration Guide](/opt/kasaai/apps/architecture/INTEGRATION_GUIDE.md)

---

**Document History**

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-24 | AI Labs Africa | Initial PRD creation |

**Approval**

| Role | Name | Signature | Date |
|------|------|-----------|------|
| Product Owner | _______________ | _______________ | ________ |
| Technical Lead | _______________ | _______________ | ________ |
| Church Stakeholder | _______________ | _______________ | ________ |

---

**End of Document**
